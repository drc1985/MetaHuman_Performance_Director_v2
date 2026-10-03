# Copyright (c) 2026 David Cobbins / Frontier Mindworks. All Rights Reserved.
# MetaHuman Performance Director (MHPD) — Batch Take Recorder & Renderer.

import unreal
import os
import sys
import glob
import shutil
import subprocess
import json
import tempfile
import math
import time
import re
from datetime import datetime
from pathlib import Path

# Resolve default output directory
DEFAULT_PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
# Fallback to repo Test/Review_v0.3.0 folder
REPO_REVIEW_DIR = Path(r"e:\DavidCobbinsGlobal\Software\MetaHumanPerformanceDirector\MetaHumanPerformanceDirector\Test\Review_v0.3.0")
DEFAULT_OUTPUT_DIR = REPO_REVIEW_DIR if REPO_REVIEW_DIR.exists() else (DEFAULT_PROJECT_DIR / "Saved" / "VideoCaptures")

DEFAULT_RENDER_MAP = "/Game/DevBuild"
REVIEW_CAMERA_PULLBACK = 1.65
REVIEW_CAMERA_HEIGHT_OFFSET = -18.0


def _safe_filename_token(value: str, fallback: str = "untitled") -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", str(value or "").strip())
    value = re.sub(r"\s+", "_", value)
    value = re.sub(r"_+", "_", value).strip(" ._")
    return value or fallback


def _resolve_output_path(output_dir: str, template: str, tokens: dict[str, str]) -> str:
    """Resolves naming tokens and always avoids overwriting an existing MP4."""
    raw_template = str(template or "{take}_{version}").strip()
    if raw_template.lower().endswith(".mp4"):
        raw_template = raw_template[:-4]

    safe_tokens = {key: _safe_filename_token(value, key) for key, value in tokens.items()}
    safe_tokens["date"] = datetime.now().strftime("%Y-%m-%d")

    has_version_token = "{version}" in raw_template

    def render(version_number: int) -> str:
        values = dict(safe_tokens)
        values["version"] = f"v{version_number:03d}"
        resolved = raw_template
        for key, value in values.items():
            resolved = resolved.replace("{" + key + "}", value)
        safe_name = _safe_filename_token(resolved)
        if not has_version_token and version_number > 1:
            safe_name += f"_v{version_number:03d}"
        return safe_name + ".mp4"

    version = 1
    candidate = os.path.join(output_dir, render(version))
    while os.path.exists(candidate):
        version += 1
        candidate = os.path.join(output_dir, render(version))
        if version > 9999:
            raise RuntimeError("Could not allocate a unique render filename.")
    return candidate

unreal.log("[MHPD Batch Render] >>> Module batch_render_takes loaded (v0.4.0 - Movie Render Queue) <<<")

def get_ffmpeg_path() -> str | None:
    """Finds ffmpeg executable on PATH or common Winget locations."""
    # Check PATH
    p = shutil.which("ffmpeg")
    if p:
        return p
    # Check default Windows Winget location
    winget_glob = glob.glob(r"C:\Users\*\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg*\ffmpeg*\bin\ffmpeg.exe")
    if winget_glob:
        return winget_glob[0]
    return None

def compile_frames_to_mp4(frame_dir: str, output_mp4: str, audio_path: str | None = None, fps: int = 30) -> bool:
    """Compiles captured JPG frames and optional audio track into a high-quality H.264 MP4."""
    ffmpeg_exe = get_ffmpeg_path()
    if not ffmpeg_exe:
        unreal.log_warning(f"[MHPD Batch Render] ffmpeg not found. JPG frames preserved in: {frame_dir}")
        return False

    jpg_files = sorted(
        glob.glob(os.path.join(frame_dir, "*.jpg")) +
        glob.glob(os.path.join(frame_dir, "*.jpeg"))
    )
    if not jpg_files:
        unreal.log_error(f"[MHPD Batch Render] No frames found in {frame_dir}")
        return False

    # Standardize frame names to seq_%05d.jpg to prevent sequence gaps or negative index issues in ffmpeg
    for idx, f in enumerate(jpg_files):
        target_path = os.path.join(frame_dir, f"seq_{idx:05d}.jpg")
        if f != target_path:
            try:
                os.rename(f, target_path)
            except Exception:
                pass

    pattern = os.path.join(frame_dir, "seq_%05d.jpg")

    cmd = [
        ffmpeg_exe,
        "-y",
        "-framerate", str(fps),
        "-i", pattern,
    ]

    if audio_path and os.path.exists(audio_path):
        unreal.log(f"[MHPD Batch Render] Muxing audio track: {audio_path}")
        cmd.extend([
            "-i", audio_path,
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest"
        ])
    else:
        cmd.extend([
            "-c:v", "libx264",
            "-pix_fmt", "yuv420p",
            "-crf", "18",
            "-preset", "fast"
        ])

    cmd.append(output_mp4)

    unreal.log(f"[MHPD Batch Render] Encoding MP4: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if res.returncode == 0 and os.path.exists(output_mp4):
            unreal.log(f"[MHPD Batch Render] ✓ Successfully generated MP4: {output_mp4}")
            # Clean up temporary frames directory
            try:
                shutil.rmtree(frame_dir)
            except Exception as e:
                unreal.log_warning(f"[MHPD Batch Render] Could not remove temp frames: {e}")
            return True
        else:
            unreal.log_error(f"[MHPD Batch Render] ffmpeg failed: {res.stderr}")
            return False
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] ffmpeg exception: {e}")
        return False


def _actor_has_metahuman_face(actor) -> bool:
    """Matches the component-based MetaHuman test used by the C++ module."""
    if not actor:
        return False

    actors_to_check = [actor]
    try:
        for child_component in actor.get_components_by_class(unreal.ChildActorComponent):
            try:
                child_actor = child_component.get_child_actor()
            except Exception:
                child_actor = child_component.get_editor_property("child_actor")
            if child_actor:
                actors_to_check.append(child_actor)
    except Exception:
        pass

    for candidate in actors_to_check:
        try:
            components = candidate.get_components_by_class(unreal.SkeletalMeshComponent)
        except Exception:
            components = []
        for component in components:
            component_name = str(component.get_name() or "").lower()
            mesh_name = ""
            try:
                mesh = component.get_editor_property("skeletal_mesh_asset")
                mesh_name = str(mesh.get_name() if mesh else "").lower()
            except Exception:
                try:
                    mesh = component.get_editor_property("skeletal_mesh")
                    mesh_name = str(mesh.get_name() if mesh else "").lower()
                except Exception:
                    pass
            if component_name == "face" or "facemesh" in mesh_name:
                return True
    return False


def _find_metahuman_actor(actor_subsystem):
    """Finds the active MetaHuman, preferring Hale when multiple actors exist."""
    if not actor_subsystem:
        return None

    matches = []
    for actor in actor_subsystem.get_all_level_actors():
        if not _actor_has_metahuman_face(actor):
            continue
        try:
            identity = f"{actor.get_actor_label()} {actor.get_name()} {actor.get_class().get_name()}".lower()
        except Exception:
            identity = str(actor.get_name() or "").lower()
        priority = 100 if "hale" in identity else 0
        matches.append((priority, identity, actor))

    if not matches:
        return None
    matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    selected = matches[0][2]
    unreal.log(
        f"[MHPD Batch Render] Selected MetaHuman actor: "
        f"{selected.get_actor_label()} ({selected.get_name()}) at {selected.get_actor_location()}"
    )
    return selected


def _get_metahuman_skeletal_components(actor) -> list:
    actors_to_check = [actor]
    try:
        for child_component in actor.get_components_by_class(unreal.ChildActorComponent):
            try:
                child_actor = child_component.get_child_actor()
            except Exception:
                child_actor = child_component.get_editor_property("child_actor")
            if child_actor:
                actors_to_check.append(child_actor)
    except Exception:
        pass

    components = []
    for candidate in actors_to_check:
        try:
            components.extend(candidate.get_components_by_class(unreal.SkeletalMeshComponent))
        except Exception:
            pass
    return components


def _find_landmark_socket(components: list, names: tuple[str, ...]):
    for component in components:
        for name in names:
            try:
                socket_name = unreal.Name(name)
                if component.does_socket_exist(socket_name):
                    location = component.get_socket_location(socket_name)
                    if location:
                        return location
            except Exception:
                pass
    return None


def _derive_anatomical_landmarks(actor) -> dict | None:
    """Derives performer-specific framing landmarks from live skeletal components."""
    components = _get_metahuman_skeletal_components(actor)
    if not components:
        return None

    component_bounds = []
    face_bounds = []
    bounds_errors = []
    for component in components:
        try:
            origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
            if float(extent.z) <= 1.0:
                continue
            bounds = (float(origin.z - extent.z), float(origin.z + extent.z))
            component_bounds.append(bounds)
            component_name = str(component.get_name() or "").lower()
            mesh_name = ""
            try:
                mesh = component.get_editor_property("skeletal_mesh_asset")
                mesh_name = str(mesh.get_name() if mesh else "").lower()
            except Exception:
                pass
            if component_name == "face" or "facemesh" in mesh_name:
                face_bounds.append(bounds)
        except Exception as exc:
            bounds_errors.append(f"{component.get_name()}: {exc}")

    if not component_bounds:
        if bounds_errors:
            unreal.log_warning(
                "[MHPD Batch Render] Skeletal component bounds failed: " + " | ".join(bounds_errors[:4])
            )
        return None

    full_bottom = min(bounds[0] for bounds in component_bounds)
    full_top = max(bounds[1] for bounds in component_bounds)
    full_height = max(100.0, full_top - full_bottom)

    face_bottom = max(full_bottom + full_height * 0.65, full_top - full_height * 0.24)
    face_top = full_top
    for candidate_bottom, candidate_top in face_bounds:
        candidate_height = candidate_top - candidate_bottom
        if 25.0 <= candidate_height <= 70.0 and abs(candidate_top - full_top) <= full_height * 0.18:
            face_bottom, face_top = candidate_bottom, candidate_top
            break

    head_height = max(32.0, min(65.0, face_top - face_bottom))
    crown_z = face_top
    chin_z = crown_z - head_height

    left_eye = _find_landmark_socket(components, (
        "FACIAL_L_Eye", "FACIAL_L_EyelidUpperA", "eye_l", "EyeLeft"))
    right_eye = _find_landmark_socket(components, (
        "FACIAL_R_Eye", "FACIAL_R_EyelidUpperA", "eye_r", "EyeRight"))
    if left_eye and right_eye:
        eye_z = (float(left_eye.z) + float(right_eye.z)) * 0.5
    elif left_eye or right_eye:
        eye_z = float((left_eye or right_eye).z)
    else:
        eye_z = chin_z + head_height * 0.62

    clavicle_l = _find_landmark_socket(components, ("clavicle_l", "upperarm_l"))
    clavicle_r = _find_landmark_socket(components, ("clavicle_r", "upperarm_r"))
    if clavicle_l and clavicle_r:
        shoulder_z = (float(clavicle_l.z) + float(clavicle_r.z)) * 0.5
    elif clavicle_l or clavicle_r:
        shoulder_z = float((clavicle_l or clavicle_r).z)
    else:
        shoulder_z = full_bottom + full_height * 0.79
    chest_z = shoulder_z - max(12.0, head_height * 0.42)

    landmarks = {
        "bottom": full_bottom,
        "top": full_top,
        "crown": crown_z,
        "eyes": eye_z,
        "chin": chin_z,
        "shoulders": shoulder_z,
        "chest": chest_z,
        "head_height": head_height,
    }
    unreal.log(f"[MHPD Batch Render] Anatomical landmarks for {actor.get_actor_label()}: {landmarks}")
    return landmarks


def _get_anatomical_camera_transform(actor, shot_preset: str, camera_angle: str, focal_length: float):
    landmarks = _derive_anatomical_landmarks(actor)
    if not landmarks:
        return None

    shot_key = str(shot_preset or "mcu").lower()
    crown = landmarks["crown"]
    eyes = landmarks["eyes"]
    chin = landmarks["chin"]
    head_height = landmarks["head_height"]

    if shot_key == "wide":
        frame_bottom, frame_top, fill = landmarks["bottom"], crown + head_height * 0.08, 0.78
    elif shot_key == "mcu":
        frame_bottom, frame_top, fill = landmarks["chest"], crown + head_height * 0.07, 0.76
    elif shot_key == "cu":
        frame_bottom, frame_top, fill = chin - head_height * 0.05, crown + head_height * 0.06, 0.76
    else:  # ECU centers the ocular performance region rather than the actor origin.
        frame_bottom, frame_top, fill = eyes - head_height * 0.20, eyes + head_height * 0.24, 0.72

    framed_height = max(12.0, frame_top - frame_bottom)
    visible_world_height = framed_height / fill
    sensor_height_mm = 13.365  # UE CineCamera 16:9 default filmback height.
    vertical_fov = 2.0 * math.atan(sensor_height_mm / (2.0 * max(1.0, float(focal_length))))
    camera_distance = visible_world_height / (2.0 * math.tan(vertical_fov * 0.5))
    camera_distance = max(55.0, min(2500.0, camera_distance))

    if shot_key == "wide":
        target_z = (frame_bottom + frame_top) * 0.5
    elif shot_key == "mcu":
        target_z = eyes - visible_world_height * 0.12
    elif shot_key == "cu":
        target_z = eyes - visible_world_height * 0.08
    else:
        target_z = eyes

    actor_loc = actor.get_actor_location()
    actor_rot = actor.get_actor_rotation()
    angle_key = str(camera_angle or "front").strip().lower()
    yaw_offset = 0.0 if angle_key == "profile" else 90.0
    yaw_radians = math.radians(float(actor_rot.yaw) + yaw_offset)
    direction = unreal.Vector(math.cos(yaw_radians), math.sin(yaw_radians), 0.0)

    elevation_degrees = 12.0 if angle_key == "high" else (-10.0 if angle_key == "low" else 0.0)
    elevation_radians = math.radians(elevation_degrees)
    horizontal_distance = camera_distance * math.cos(elevation_radians)
    target = unreal.Vector(actor_loc.x, actor_loc.y, target_z)
    cam_loc = target + (direction * horizontal_distance)
    cam_loc.z += camera_distance * math.sin(elevation_radians)

    look_delta = target - cam_loc
    horizontal_look = math.hypot(float(look_delta.x), float(look_delta.y))
    cam_rot = unreal.Rotator(
        pitch=math.degrees(math.atan2(float(look_delta.z), horizontal_look)),
        yaw=math.degrees(math.atan2(float(look_delta.y), float(look_delta.x))),
        roll=12.0 if angle_key == "dutch" else 0.0,
    )
    unreal.log(
        f"[MHPD Batch Render] Anatomy-framed {shot_key}/{angle_key}: focal={focal_length:.1f}mm, "
        f"span=({frame_bottom:.1f},{frame_top:.1f}), targetZ={target_z:.1f}, distance={camera_distance:.1f}cm"
    )
    return cam_loc, cam_rot

def get_optimal_camera_transform(
    pullback: float | None = None,
    height_offset: float | None = None,
    camera_angle: str = "front",
) -> tuple[unreal.Vector, unreal.Rotator]:
    """Calculates the optimal camera transform targeting the MetaHuman face, respecting framing pullback and height."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    actual_pullback = REVIEW_CAMERA_PULLBACK if pullback is None else float(pullback)
    actual_height_offset = REVIEW_CAMERA_HEIGHT_OFFSET if height_offset is None else float(height_offset)

    mh_actor = _find_metahuman_actor(actor_subsystem)

    # Verified framing in DevBuild:
    # MH actor at (36820.0, -7930.0, 10.0), face at Z = 168.7.
    # Camera at (36740.2, -8034.4, 168.7), Pitch=4.2, Yaw=54.6, Roll=0.0 directly faces character (131cm distance).
    DEFAULT_CAM_LOC = unreal.Vector(36740.2, -8034.4, 168.7)
    DEFAULT_CAM_ROT = unreal.Rotator(pitch=4.2, yaw=54.6, roll=0.0)

    # Place the review camera in front of the selected MetaHuman. Actor yaw is
    # authoritative; editor viewport position and legacy DevBuild coordinates
    # are unrelated to characters staged in other maps such as Fireside_Custom.
    if mh_actor:
        mh_loc = mh_actor.get_actor_location()
        actor_rot = mh_actor.get_actor_rotation()
        # MetaHuman meshes face local +Y, while Actor forward is local +X.
        angle_key = str(camera_angle or "front").strip().lower()
        camera_yaw_offset = 0.0 if angle_key == "profile" else 90.0
        actor_yaw_radians = math.radians(float(actor_rot.yaw) + camera_yaw_offset)
        face_direction = unreal.Vector(
            math.cos(actor_yaw_radians),
            math.sin(actor_yaw_radians),
            0.0,
        )

        face_anchor = unreal.Vector(mh_loc.x, mh_loc.y, mh_loc.z + 158.7)
        camera_distance = 131.3 * actual_pullback
        cam_loc = face_anchor + (face_direction * camera_distance)
        cam_loc.z += actual_height_offset
        if angle_key == "low":
            cam_loc.z -= 30.0
        elif angle_key == "high":
            cam_loc.z += 35.0

        look_delta = face_anchor - cam_loc
        horizontal_distance = math.hypot(float(look_delta.x), float(look_delta.y))
        cam_rot = unreal.Rotator(
            pitch=math.degrees(math.atan2(float(look_delta.z), horizontal_distance)),
            yaw=math.degrees(math.atan2(float(look_delta.y), float(look_delta.x))),
            roll=12.0 if angle_key == "dutch" else 0.0,
        )
        unreal.log(
            f"[MHPD Batch Render] Actor-relative frontal camera for {mh_actor.get_actor_label()}: "
            f"ActorRot={actor_rot}, Angle={angle_key}, Loc={cam_loc}, LookAt={face_anchor}, Rot={cam_rot}"
        )
        return cam_loc, cam_rot
    # 3. Fallback to verified DevBuild constants
    default_face_anchor = unreal.Vector(36820.0, -7930.0, 168.7)
    default_offset = DEFAULT_CAM_LOC - default_face_anchor
    wide_default_loc = default_face_anchor + (default_offset * actual_pullback)
    wide_default_loc.z += actual_height_offset
    unreal.log(f"[MHPD Batch Render] Using default wide MCU framing -> {wide_default_loc}")
    return wide_default_loc, DEFAULT_CAM_ROT


def _set_camera_focal_length_track(
    seq_asset,
    camera_actor_binding,
    focal_length: float,
    camera_component=None,
) -> bool:
    """Persist lens state as a component property track evaluated by Sequencer/MRQ."""
    component_binding = None
    for binding in camera_actor_binding.get_child_possessables():
        binding_name = str(binding.get_name() or "").lower()
        if "camera component" in binding_name or "cameracomponent" in binding_name:
            component_binding = binding
            break

    temporary_camera = None
    if component_binding is None:
        if camera_component is None:
            actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
            temporary_camera = actor_subsystem.spawn_actor_from_class(
                unreal.CineCameraActor, unreal.Vector(), unreal.Rotator())
            if temporary_camera:
                camera_component = temporary_camera.camera_component
        if camera_component is None:
            unreal.log_error("[MHPD Batch Render] Could not create a CineCamera component binding.")
            return False
        component_binding = seq_asset.add_possessable(camera_component)
        component_binding.set_parent(camera_actor_binding)

    try:
        focal_tracks = []
        for track in component_binding.get_tracks():
            if isinstance(track, unreal.MovieSceneFloatTrack) and str(track.get_property_name()) == "CurrentFocalLength":
                focal_tracks.append(track)
        if not focal_tracks:
            focal_track = component_binding.add_track(unreal.MovieSceneFloatTrack)
            focal_track.set_property_name_and_path("CurrentFocalLength", "CurrentFocalLength")
            focal_tracks = [focal_track]

        start_frame = seq_asset.get_playback_start()
        end_frame = seq_asset.get_playback_end()
        for focal_track in focal_tracks:
            sections = focal_track.get_sections() or [focal_track.add_section()]
            for section in sections:
                section.set_range(start_frame, end_frame)
                for channel in section.get_all_channels():
                    channel.set_default(float(focal_length))
                    try:
                        for key in list(channel.get_keys()):
                            channel.remove_key(key)
                    except Exception:
                        pass
                    channel.add_key(unreal.FrameNumber(start_frame), float(focal_length))
        unreal.log(
            f"[MHPD Batch Render] ✓ Sequencer focal-length track set to {focal_length:.3f}mm "
            f"(frames {start_frame}-{end_frame})"
        )
        return True
    except Exception as exc:
        unreal.log_error(f"[MHPD Batch Render] Could not write focal-length track: {exc}")
        return False
    finally:
        if temporary_camera:
            unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(temporary_camera)


def _render_camera_binding(seq_asset):
    """Resolve the actual Camera Cut target, never a camera guessed by its name."""
    cuts = [s for t in seq_asset.get_tracks()
            if isinstance(t, unreal.MovieSceneCameraCutTrack) for s in t.get_sections()]
    if len(cuts) != 1:
        raise RuntimeError("Render Studio requires one Camera Cut. Edit/accept a single camera before rendering.")
    binding = seq_asset.find_binding_by_id(cuts[0].get_camera_binding_id().get_editor_property("guid"))
    if not binding.is_valid():
        raise RuntimeError("The Camera Cut has an unresolved camera binding. Regenerate the shot.")
    if not any(isinstance(t, unreal.MovieScene3DTransformTrack) for t in binding.get_tracks()):
        raise RuntimeError("The Camera Cut target has no camera transform track.")
    return binding


def prepare_camera_for_manual_edit(sequence_path: str, shot_preset="mcu", camera_angle="front", focal_length=0.0) -> bool:
    """Seed a missing camera, but never overwrite an existing authored camera on mode entry."""
    seq_asset = unreal.load_asset(sequence_path)
    if not seq_asset:
        raise RuntimeError(f"Could not load camera sequence: {sequence_path}")
    cuts = [s for t in seq_asset.get_tracks()
            if isinstance(t, unreal.MovieSceneCameraCutTrack) for s in t.get_sections()]
    if not cuts and not ensure_camera_cut_track(seq_asset, shot_preset=shot_preset,
                                               camera_angle=camera_angle, focal_length=focal_length):
        return False
    _render_camera_binding(seq_asset)
    return True


def _manual_camera_output_tokens(seq_asset):
    """Manual outputs must not be named after unused dropdown presets."""
    binding = _render_camera_binding(seq_asset)
    for component in binding.get_child_possessables():
        for track in component.get_tracks():
            if isinstance(track, unreal.MovieSceneFloatTrack) and str(track.get_property_name()) == "CurrentFocalLength":
                for section in track.get_sections():
                    for channel in section.get_all_channels():
                        if channel.has_default():
                            return {"shot": "manual", "angle": "manual", "lens": f"{channel.get_default():g}mm"}
    return {"shot": "manual", "angle": "manual", "lens": "saved"}


def _set_camera_optics_tracks(seq_asset, camera_binding, snapshot):
    """Persist the viewed filmback/aperture as well as focal length across PIE."""
    component_binding = next(b for b in camera_binding.get_child_possessables()
                             if "cameracomponent" in str(b.get_name()).replace(" ", "").lower())
    for prop, path, value in (
        ("SensorWidth", "Filmback.SensorWidth", snapshot["sensor_width"]),
        ("SensorHeight", "Filmback.SensorHeight", snapshot["sensor_height"]),
        ("CurrentAperture", "CurrentAperture", snapshot["aperture"]),
    ):
        track = next((t for t in component_binding.get_tracks()
                      if isinstance(t, unreal.MovieSceneFloatTrack) and t.get_property_path() == path), None)
        if track is None:
            track = component_binding.add_track(unreal.MovieSceneFloatTrack)
            track.set_property_name_and_path(prop, path)
        for section in track.get_sections() or [track.add_section()]:
            section.set_range(seq_asset.get_playback_start(), seq_asset.get_playback_end())
            for channel in section.get_all_channels():
                for key in list(channel.get_keys()):
                    channel.remove_key(key)
                channel.set_default(float(value))
                channel.add_key(unreal.FrameNumber(seq_asset.get_playback_start()), float(value))


_LOOK_TRACK_PREFIX = "MHPD Look: "


def _validated_look(look: str, look_intensity: float):
    key = str(look or "clean").strip().lower()
    strength = float(look_intensity)
    if key not in ("clean", "noir") or not math.isfinite(strength) or not 0.0 <= strength <= 1.0:
        raise ValueError("Look must be Clean or Noir, with intensity between 0 and 1.")
    return key, strength


def _noir_properties(strength):
    # RGB multipliers stay neutral; W supplies global saturation/contrast.
    # Modest contrast/grain retain facial detail. No exposure, lights, DoF or pose changes.
    return {
        "ColorSaturation": (1.0, 1.0, 1.0, 1.0 - strength),
        "ColorContrast": (1.0, 1.0, 1.0, 1.0 + 0.18 * strength),
        "VignetteIntensity": 0.20 + 0.15 * strength,
        "FilmGrainIntensity": 0.12 * strength,
        "BloomIntensity": 0.25,
    }


def apply_camera_look_to_sequence(sequence_path: str, look="clean", look_intensity=1.0,
                                  save_asset=True) -> bool:
    """Camera-local finishing tracks. Never rebuild camera pose/lens or change stage lights.

    Clean removes only MHPD-owned look tracks; it does not neutralize the environment
    or overwrite unrelated authored grading. Explicit grading-track conflicts fail.
    """
    key, strength = _validated_look(look, look_intensity)
    seq = unreal.load_asset(sequence_path)
    if not seq:
        raise RuntimeError(f"Look sequence not found: {sequence_path}")
    camera = _render_camera_binding(seq)
    components = [b for b in camera.get_child_possessables()
                  if "cameracomponent" in str(b.get_name()).replace(" ", "").lower()]
    if len(components) != 1:
        raise RuntimeError("Look requires one resolved CineCamera component binding.")
    component = components[0]
    existing = list(component.get_tracks())
    owned = [t for t in existing if str(t.get_display_name()).startswith(_LOOK_TRACK_PREFIX)]
    enabled = key == "noir" and strength > 0.0
    values = _noir_properties(strength)
    paths = {"PostProcessBlendWeight"}
    paths.update("PostProcessSettings." + prop for prop in values)
    paths.update("PostProcessSettings.bOverride_" + prop for prop in values)
    if enabled:
        conflicts = [str(t.get_property_path()) for t in existing
                     if t not in owned and isinstance(t, unreal.MovieScenePropertyTrack)
                     and str(t.get_property_path()) in paths]
        if conflicts:
            raise RuntimeError("Noir would conflict with authored camera grading tracks: " + ", ".join(conflicts))

    # Stage replacement tracks first; a scripting failure must not discard the
    # previously accepted look or leave a partially-authored effect behind.
    staged = []
    if enabled:
        specifications = [("PostProcessBlendWeight", unreal.MovieSceneFloatTrack, [1.0])]
        for prop, value in values.items():
            specifications.append(("PostProcessSettings.bOverride_" + prop, unreal.MovieSceneBoolTrack, [True]))
            specifications.append(("PostProcessSettings." + prop,
                                   unreal.MovieSceneDoubleVectorTrack if isinstance(value, tuple) else unreal.MovieSceneFloatTrack,
                                   list(value) if isinstance(value, tuple) else [value]))
        try:
            for path, track_type, channel_values in specifications:
                track = component.add_track(track_type)
                staged.append(track)
                track.set_property_name_and_path(path.rsplit(".", 1)[-1], path)
                track.set_display_name(_LOOK_TRACK_PREFIX + path)
                if track_type == unreal.MovieSceneDoubleVectorTrack:
                    track.set_num_channels_used(4)
                section = track.add_section()
                section.set_range(seq.get_playback_start(), seq.get_playback_end())
                channels = section.get_all_channels()
                if len(channels) != len(channel_values):
                    raise RuntimeError(f"Look channel mismatch for {path}: {len(channels)}")
                for channel, value in zip(channels, channel_values):
                    channel.set_default(value)
                    channel.add_key(unreal.FrameNumber(seq.get_playback_start()), value)
        except Exception:
            for track in staged:
                component.remove_track(track)
            raise
    for track in owned:
        component.remove_track(track)
    unreal.EditorAssetLibrary.set_metadata_tag(seq, "MHPD.RenderLook", key)
    unreal.EditorAssetLibrary.set_metadata_tag(seq, "MHPD.RenderLookIntensity", str(strength))
    if save_asset and not unreal.EditorAssetLibrary.save_loaded_asset(seq, False):
        raise RuntimeError("Could not save camera look to the selected sequence.")
    unreal.log(f"[MHPD Batch Render] Look: {key} ({strength:.0%}); framing/lens unchanged.")
    return True


def preview_manual_camera_look(sequence_path: str, camera_actor_path: str,
                               look="clean", look_intensity=1.0) -> bool:
    """Apply the same look to the independent editor pilot without touching the take.

    Use the source template for restoration, not its currently evaluated Noir state.
    """
    key, strength = _validated_look(look, look_intensity)
    seq = unreal.load_asset(sequence_path)
    actor = unreal.find_object(None, camera_actor_path)
    if not seq or not isinstance(actor, unreal.CineCameraActor) or not actor.get_editor_property("is_editor_only_actor"):
        raise RuntimeError("Manual look preview requires the active editor-only camera pilot.")
    template = _render_camera_binding(seq).get_object_template()
    if not isinstance(template, unreal.CineCameraActor):
        raise RuntimeError("Manual look preview requires a spawnable CineCamera template.")
    component = actor.camera_component
    base = template.camera_component.get_editor_property("post_process_settings")
    settings = component.get_editor_property("post_process_settings")
    values = _noir_properties(strength)
    enabled = key == "noir" and strength > 0.0
    for prop, value in values.items():
        # Unreal Python editor properties use snake_case reflected names.
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", prop).lower()
        settings.set_editor_property("override_" + name, True if enabled else base.get_editor_property("override_" + name))
        settings.set_editor_property(name, unreal.Vector4(*value) if enabled and isinstance(value, tuple)
                                     else value if enabled else base.get_editor_property(name))
    component.set_editor_property("post_process_settings", settings)
    component.set_editor_property("post_process_blend_weight", 1.0 if enabled
                                  else template.camera_component.get_editor_property("post_process_blend_weight"))
    return True


def ensure_camera_cut_track(
    seq_asset,
    framing_scale: float | None = None,
    shot_preset: str = "",
    camera_angle: str = "front",
    focal_length: float = 0.0,
) -> bool:
    """Ensures the sequence has a spawnable CineCameraActor and Camera Cuts track framed on the MetaHuman face."""
    if not seq_asset:
        unreal.log_error("[MHPD Batch Render] ensure_camera_cut_track received null seq_asset.")
        return False

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not actor_subsystem:
        unreal.log_error("[MHPD Batch Render] Could not get EditorActorSubsystem.")
        return False

    # 1. Clean up any existing Camera Cut tracks in the sequence
    for t in list(seq_asset.get_tracks()):
        if isinstance(t, unreal.MovieSceneCameraCutTrack):
            seq_asset.remove_track(t)
            unreal.log(f"[MHPD Batch Render] Cleared existing CameraCutTrack from '{seq_asset.get_name()}'.")

    # 2. Clean up any existing camera bindings in the sequence (possessables or spawnables)
    for b in list(seq_asset.get_bindings()):
        b_name = str(b.get_name() or "")
        try:
            b_disp = str(b.get_display_name() or "")
        except Exception:
            b_disp = ""
        b_full = f"{b_name} {b_disp}".lower()
        if any(keyword in b_full for keyword in ("cinecamera", "reviewcamera", "camera")):
            try:
                b.remove()
                unreal.log(f"[MHPD Batch Render] Cleared existing camera binding: {b_name}")
            except Exception as e:
                unreal.log_warning(f"[MHPD Batch Render] Could not remove old binding '{b_name}': {e}")

    # 3. Clean up any stale editor-spawned MHPD_ReviewCamera actors in the level
    for a in list(actor_subsystem.get_all_level_actors()):
        if isinstance(a, unreal.CineCameraActor) and ("MHPD_ReviewCamera" in a.get_name() or "MHPD_ReviewCamera" in a.get_actor_label()):
            actor_subsystem.destroy_actor(a)

    # Resolve framing_scale from parameter or cached plan JSON
    seq_name = seq_asset.get_name()
    take_key = seq_name[3:] if seq_name.startswith("LS_") else seq_name
    if framing_scale is None:
        plan_file = os.path.join(tempfile.gettempdir(), f"mhpd_plan_{take_key}.json")
        if os.path.exists(plan_file):
            try:
                with open(plan_file, "r", encoding="utf-8") as pf:
                    p_data = json.load(pf)
                    framing_scale = float(p_data.get("framing_scale", 0.50))
            except Exception:
                framing_scale = 0.50

    shot_key = str(shot_preset or "").strip().lower()
    explicit_shots = {
        "wide": (35.0, 2.80, -24.0, "Master / Wide"),
        # Leave enough headroom for taller MetaHumans and visible upper chest.
        "mcu": (52.0, 1.80, -16.0, "Medium Close-Up"),
        "cu": (85.0, 1.70, -12.0, "Dramatic Close-Up"),
        "ecu": (105.0, 1.35, -8.0, "Extreme Close-Up"),
    }
    scale_val = 0.50 if framing_scale is None else float(framing_scale)
    if shot_key in explicit_shots:
        target_focal_length, scale_pullback, scale_height_offset, shot_label = explicit_shots[shot_key]
        unreal.log(
            f"[MHPD Batch Render] Render Studio shot '{shot_label}' -> "
            f"{target_focal_length:.0f}mm, pullback {scale_pullback:.2f}, height {scale_height_offset:.0f}cm"
        )
    elif scale_val <= 0.20:
        target_focal_length = 55.0
        scale_pullback = 1.30
        scale_height_offset = -12.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Close-Up (55mm, pullback 1.30, height -12cm)")
    elif scale_val <= 0.40:
        target_focal_length = 52.0
        scale_pullback = 1.80
        scale_height_offset = -16.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Medium Close-Up (52mm, pullback 1.80, height -16cm)")
    elif scale_val >= 0.70:
        target_focal_length = 35.0
        scale_pullback = 2.00
        scale_height_offset = -20.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Theatrical Wide (35mm, pullback 2.00, height -20cm)")
    else:
        target_focal_length = 50.0
        scale_pullback = REVIEW_CAMERA_PULLBACK
        scale_height_offset = REVIEW_CAMERA_HEIGHT_OFFSET

    requested_focal_length = float(focal_length or 0.0)
    if requested_focal_length > 0.0:
        # Preserve the chosen composition when changing lenses by scaling camera distance
        # proportionally. This changes perspective without unexpectedly cropping the actor.
        scale_pullback *= requested_focal_length / target_focal_length
        target_focal_length = requested_focal_length

    # 4. Determine camera location and rotation. Explicit Render Studio shots use
    # performer-specific anatomy; legacy framing_scale jobs retain the verified fallback.
    anatomy_transform = None
    if shot_key in explicit_shots:
        mh_actor = _find_metahuman_actor(actor_subsystem)
        if mh_actor:
            anatomy_transform = _get_anatomical_camera_transform(
                mh_actor,
                shot_key,
                camera_angle,
                target_focal_length,
            )
    if anatomy_transform:
        cam_loc, cam_rot = anatomy_transform
    else:
        unreal.log_warning(
            "[MHPD Batch Render] Anatomical landmarks unavailable; using legacy actor-relative framing fallback."
        )
        cam_loc, cam_rot = get_optimal_camera_transform(
            pullback=scale_pullback,
            height_offset=scale_height_offset,
            camera_angle=camera_angle,
        )

    # 5. Spawn temporary CineCameraActor to configure template for Sequencer spawnable
    temp_cam = actor_subsystem.spawn_actor_from_class(unreal.CineCameraActor, cam_loc, cam_rot)
    if not temp_cam:
        unreal.log_error("[MHPD Batch Render] Failed to spawn temporary CineCameraActor.")
        return False

    temp_cam.set_actor_label("MHPD_ReviewCamera")
    try:
        cam_comp = temp_cam.camera_component
        cam_comp.current_focal_length = target_focal_length
        cam_comp.focus_settings.focus_method = unreal.CameraFocusMethod.DISABLE
    except Exception as e:
        unreal.log_warning(f"[MHPD Batch Render] Could not configure camera component: {e}")

    # 6. Add camera as SPAWNABLE to the LevelSequence (ensures persistence into PIE)
    cam_binding = seq_asset.add_spawnable_from_instance(temp_cam)

    if not cam_binding or not cam_binding.is_valid():
        actor_subsystem.destroy_actor(temp_cam)
        unreal.log_error(f"[MHPD Batch Render] Failed to create spawnable camera binding in '{seq_asset.get_name()}'.")
        return False

    # The CineCameraActor spawnable template does not serialize its component lens
    # reliably in UE 5.8. A child component property track is the authoritative lens
    # state that Sequencer and MRQ both evaluate.
    if not _set_camera_focal_length_track(
        seq_asset, cam_binding, target_focal_length, temp_cam.camera_component
    ):
        actor_subsystem.destroy_actor(temp_cam)
        return False

    # 7. Destroy temporary level actor after its component binding has been authored.
    actor_subsystem.destroy_actor(temp_cam)

    start_frame = seq_asset.get_playback_start()
    end_frame = seq_asset.get_playback_end()

    # 8. Configure MovieSceneSpawnTrack so Sequencer actually spawns the CineCameraActor during PIE
    try:
        spawn_tracks = [t for t in cam_binding.get_tracks() if isinstance(t, unreal.MovieSceneSpawnTrack)]
        if not spawn_tracks:
            st = cam_binding.add_track(unreal.MovieSceneSpawnTrack)
            spawn_tracks = [st]
        for st in spawn_tracks:
            sections = st.get_sections()
            if not sections:
                sections = [st.add_section()]
            for s in sections:
                s.set_range(start_frame, end_frame)
                for channel in s.get_all_channels():
                    if isinstance(channel, unreal.MovieSceneScriptingBoolChannel):
                        channel.set_default(True)
                        try:
                            channel.add_key(unreal.FrameNumber(start_frame), True)
                        except Exception:
                            pass
        unreal.log(f"[MHPD Batch Render] ✓ Configured MovieSceneSpawnTrack on camera (frames {start_frame}-{end_frame})")
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] Could not configure spawn track for spawnable camera: {e}")
        return False

    # 9. Configure MovieScene3DTransformTrack on camera binding with explicit position and rotation
    try:
        transform_tracks = [t for t in cam_binding.get_tracks() if isinstance(t, unreal.MovieScene3DTransformTrack)]
        if not transform_tracks:
            tt = cam_binding.add_track(unreal.MovieScene3DTransformTrack)
            transform_tracks = [tt]
        for tt in transform_tracks:
            sections = tt.get_sections()
            if not sections:
                sections = [tt.add_section()]
            for transform_section in sections:
                transform_section.set_range(start_frame, end_frame)
                for channel in transform_section.get_all_channels():
                    cname = str(channel.get_name())
                    val = None
                    if cname.startswith("Location.X"):
                        val = float(cam_loc.x)
                    elif cname.startswith("Location.Y"):
                        val = float(cam_loc.y)
                    elif cname.startswith("Location.Z"):
                        val = float(cam_loc.z)
                    elif cname.startswith("Rotation.X"):
                        val = float(cam_rot.roll)
                    elif cname.startswith("Rotation.Y"):
                        val = float(cam_rot.pitch)
                    elif cname.startswith("Rotation.Z"):
                        val = float(cam_rot.yaw)

                    if val is not None:
                        channel.set_default(val)
                        try:
                            channel.add_key(unreal.FrameNumber(start_frame), val)
                        except Exception:
                            pass
        unreal.log(f"[MHPD Batch Render] ✓ Keyed MovieScene3DTransformTrack on camera: Loc={cam_loc}, Rot={cam_rot}")
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] Could not configure transform track for spawnable camera: {e}")
        return False

    # 10. Create fresh Camera Cuts track and section
    try:
        cam_cut_track = seq_asset.add_track(unreal.MovieSceneCameraCutTrack)
        cam_cut_section = cam_cut_track.add_section()
        cam_cut_section.set_range(start_frame, end_frame)

        binding_id = seq_asset.get_binding_id(cam_binding)
        try:
            cam_cut_section.set_camera_binding_id(binding_id)
        except Exception:
            cam_cut_section.set_editor_property("CameraBindingID", binding_id)

        unreal.log(f"[MHPD Batch Render] ✓ Attached spawnable CameraCutTrack to '{seq_asset.get_name()}' (frames {start_frame}-{end_frame})")
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] Failed to configure CameraCutTrack section: {e}")
        return False

    # 9. Save sequence asset to disk so PIE context reads the updated spawnable & CameraCutTrack
    try:
        saved = unreal.EditorAssetLibrary.save_loaded_asset(seq_asset, False)
        unreal.log(f"[MHPD Batch Render] Saved sequence asset to disk: {saved}")
        if not saved:
            return False
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] Could not save sequence asset: {e}")
        return False

    # 10. Refresh Sequencer UI if open
    try:
        unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
    except Exception:
        pass

    return True


def accept_adjusted_camera(sequence_path: str, camera_snapshot: str = "", look: str | None = None,
                           look_intensity: float = 1.0) -> bool:
    """Bake a single C++ snapshot of the camera actually driving the visible viewport.

    Never combine a hidden perspective viewport's pose/FOV with a locked CineCamera.
    Missing capture data is a hard failure, not a silently accepted fallback.
    """
    seq_asset = unreal.load_asset(sequence_path)
    if not seq_asset:
        unreal.log_error(f"[MHPD Batch Render] Cannot accept camera; sequence not found: {sequence_path}")
        return False

    try:
        snapshot = json.loads(camera_snapshot)
        for key in ("x", "y", "z", "pitch", "yaw", "roll", "focal_length", "sensor_width", "sensor_height", "aperture"):
            if not math.isfinite(float(snapshot[key])):
                raise ValueError(f"Invalid camera {key}")
        if min(snapshot["focal_length"], snapshot["sensor_width"], snapshot["sensor_height"], snapshot["aperture"]) <= 0:
            raise ValueError("Invalid camera optics")
        cam_loc = unreal.Vector(x=snapshot["x"], y=snapshot["y"], z=snapshot["z"])
        cam_rot = unreal.Rotator(pitch=snapshot["pitch"], yaw=snapshot["yaw"], roll=snapshot["roll"])
        captured_focal_length = float(snapshot["focal_length"])
        # A new take may only have a camera in its temporary preview. Explicit
        # acceptance must create a source Camera Cut before baking that candidate.
        has_camera_cut = any(t.get_sections() for t in seq_asset.get_tracks()
                             if isinstance(t, unreal.MovieSceneCameraCutTrack))
        if not has_camera_cut and not ensure_camera_cut_track(seq_asset, focal_length=captured_focal_length):
            raise RuntimeError("Could not create a source camera for the accepted preview.")
        camera_bindings = [_render_camera_binding(seq_asset)]
    except Exception as e:
        unreal.log_error(f"[MHPD Batch Render] Could not capture viewport camera: {e}")
        return False

    start_frame = seq_asset.get_playback_start()
    wrote_transform = False
    for binding in camera_bindings:
        for track in binding.get_tracks():
            if not isinstance(track, unreal.MovieScene3DTransformTrack):
                continue
            for section in track.get_sections():
                for channel in section.get_all_channels():
                    cname = str(channel.get_name())
                    value = None
                    if cname.startswith("Location.X"):
                        value = float(cam_loc.x)
                    elif cname.startswith("Location.Y"):
                        value = float(cam_loc.y)
                    elif cname.startswith("Location.Z"):
                        value = float(cam_loc.z)
                    elif cname.startswith("Rotation.X"):
                        value = float(cam_rot.roll)
                    elif cname.startswith("Rotation.Y"):
                        value = float(cam_rot.pitch)
                    elif cname.startswith("Rotation.Z"):
                        value = float(cam_rot.yaw)
                    if value is None:
                        continue
                    channel.set_default(value)
                    # Replace prior generated keys so an old dropdown preset cannot
                    # take control again when MRQ begins evaluating the sequence.
                    try:
                        for key in list(channel.get_keys()):
                            channel.remove_key(key)
                    except Exception:
                        pass
                    channel.add_key(unreal.FrameNumber(start_frame), value)
                    wrote_transform = True

    if not wrote_transform:
        unreal.log_error("[MHPD Batch Render] Cannot accept camera; its transform channels were unavailable.")
        return False

    # Both locked-camera and free-viewport captures must key their lens. Previously
    # the evaluated-camera branch skipped this, leaving the old preset authoritative.
    if not _set_camera_focal_length_track(seq_asset, camera_bindings[0], captured_focal_length):
        return False
    _set_camera_optics_tracks(seq_asset, camera_bindings[0], snapshot)

    if look is not None:
        apply_camera_look_to_sequence(sequence_path, look, look_intensity, save_asset=False)

    saved = unreal.EditorAssetLibrary.save_loaded_asset(seq_asset, False)
    try:
        unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
    except Exception:
        pass
    unreal.log(
        f"[MHPD Batch Render] ✓ Accepted visible viewport as authored camera: "
        f"Source={snapshot.get('source', 'unknown')}, Loc={cam_loc}, Rot={cam_rot}, "
        f"Focal={captured_focal_length:.3f}mm, saved={saved}"
    )
    return bool(saved)


def create_shot_preview(
    sequence_path: str,
    preview_asset_path: str,
    shot_preset: str = "mcu",
    camera_angle: str = "front",
    focal_length: float = 0.0,
    look: str = "clean",
    look_intensity: float = 1.0,
) -> bool:
    """Creates an isolated Level Sequence copy for non-destructive shot previewing."""
    source_asset = unreal.load_asset(sequence_path)
    if not source_asset:
        unreal.log_error(f"[MHPD Batch Render] Preview source sequence not found: {sequence_path}")
        return False

    destination = str(preview_asset_path or "").split(".", 1)[0]
    if not destination:
        unreal.log_error("[MHPD Batch Render] Preview destination path is empty.")
        return False

    try:
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            unreal.EditorAssetLibrary.delete_asset(destination)
        preview_asset = unreal.EditorAssetLibrary.duplicate_loaded_asset(source_asset, destination)
        if not preview_asset:
            unreal.log_error(f"[MHPD Batch Render] Could not duplicate preview sequence to {destination}")
            return False
        if not ensure_camera_cut_track(
            preview_asset,
            shot_preset=shot_preset,
            camera_angle=camera_angle,
            focal_length=focal_length,
        ):
            return False
        apply_camera_look_to_sequence(preview_asset.get_path_name(), look, look_intensity)
        unreal.log(f"[MHPD Batch Render] Shot preview ready: {preview_asset.get_path_name()}")
        return True
    except Exception as exc:
        unreal.log_error(f"[MHPD Batch Render] Failed to create shot preview: {exc}")
        return False


def get_audio_source_from_sequence(seq_asset) -> str | None:
    """Extracts disk WAV filepath associated with sequence's DialogueAudio track."""
    for t in seq_asset.get_tracks():
        if isinstance(t, unreal.MovieSceneAudioTrack):
            for s in t.get_sections():
                sound = s.get_editor_property("sound")
                if sound:
                    import_data = sound.get_editor_property("asset_import_data")
                    if import_data:
                        first_file = import_data.get_first_filename()
                        if first_file and os.path.exists(first_file):
                            return first_file
    # Fallback to repo outputs/
    default_voice = r"E:\DavidCobbinsGlobal\Software\MetaHumanPerformanceDirector\outputs\fearful_female_american_voiceover.wav"
    if os.path.exists(default_voice):
        return default_voice
    return None


def _get_render_map_path() -> str:
    """Returns the active saved stage, falling back to DevBuild."""
    try:
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor_subsystem.get_editor_world() if editor_subsystem else None
        if world:
            package_path = str(world.get_outermost().get_name())
            if package_path.startswith("/Game/"):
                unreal.log(f"[MHPD Batch Render] Using active review map: {package_path}")
                return package_path
    except Exception as e:
        unreal.log_warning(f"[MHPD Batch Render] Could not resolve active map: {e}")
    unreal.log_warning(f"[MHPD Batch Render] Falling back to review map: {DEFAULT_RENDER_MAP}")
    return DEFAULT_RENDER_MAP


def create_mrq_job(sequence_path: str, output_frame_dir: str, res_x: int = 1920,
                   res_y: int = 1080, fps: int = 30, quality_preset: int = 1):
    """
    Creates one MRQ job that evaluates the sequence and its camera cuts in PIE.
    Quality Presets (§2):
      0 = Draft Preview (1080p, 10 warm-up frames)
      1 = Production Hero (1440p/QHD, 32 warm-up frames, 4x spatial AA)
      2 = Cinematic Master (4K UHD, 32 warm-up frames, 4x spatial AA)
    """
    subsystem = unreal.get_editor_subsystem(unreal.MoviePipelineQueueSubsystem)
    if not subsystem:
        raise RuntimeError("Movie Render Queue subsystem is unavailable. Enable the Movie Render Pipeline plugin.")
    queue = subsystem.get_queue()
    if subsystem.is_rendering():
        raise RuntimeError("Movie Render Queue is already rendering another job.")
    foreign_jobs = [job for job in queue.get_jobs() if str(job.author).strip() and str(job.author) != "MetaHuman Performance Director"]
    if foreign_jobs:
        raise RuntimeError("Movie Render Queue contains user jobs. Clear or render them before starting an MHPD batch.")
    queue.delete_all_jobs()
    job = queue.allocate_new_job(unreal.MoviePipelineExecutorJob)
    job.author = "MetaHuman Performance Director"
    job.job_name = f"MHPD_{Path(sequence_path).name}"
    seq_str = str(sequence_path)
    if "." not in seq_str.split("/")[-1]:
        seq_str = f"{seq_str}.{seq_str.split('/')[-1]}"
    map_str = _get_render_map_path()
    if "." not in map_str.split("/")[-1]:
        map_str = f"{map_str}.{map_str.split('/')[-1]}"

    job.set_editor_property("sequence", unreal.SoftObjectPath(path_string=seq_str))
    job.set_editor_property("map", unreal.SoftObjectPath(path_string=map_str))
    config = job.get_configuration()
    output = config.find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
    output.output_directory = unreal.DirectoryPath(output_frame_dir)
    output.file_name_format = "frame_{frame_number}"

    # Resolve resolution and warm-up counts from quality preset
    if quality_preset == 0:
        actual_res_x, actual_res_y = 1920, 1080
        warm_up = 10
        spatial_aa, temporal_aa = 1, 1
        unreal.log("[MHPD Batch Render] Applying 'Draft Preview' preset (1080p, 10 warm-up frames)")
    elif quality_preset == 2:
        actual_res_x, actual_res_y = 3840, 2160
        warm_up = 32
        spatial_aa, temporal_aa = 4, 1
        unreal.log("[MHPD Batch Render] Applying 'Cinematic Master' preset (4K UHD, 32 warm-up frames, 4x spatial AA; thermal-safe)")
    else:  # ProductionHero (Default 1)
        actual_res_x, actual_res_y = 2560, 1440
        warm_up = 32
        spatial_aa, temporal_aa = 4, 1
        unreal.log("[MHPD Batch Render] Applying 'Production Hero' preset (1440p QHD, 32 warm-up frames, 4x spatial AA)")

    output.output_resolution = unreal.IntPoint(actual_res_x, actual_res_y)
    output.use_custom_frame_rate = True
    output.output_frame_rate = unreal.FrameRate(fps, 1)
    output.flush_disk_writes_per_shot = True
    config.find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
    config.find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_JPG)
    anti_aliasing = config.find_or_add_setting_by_class(unreal.MoviePipelineAntiAliasingSetting)
    anti_aliasing.engine_warm_up_count = warm_up
    anti_aliasing.render_warm_up_count = warm_up
    try:
        anti_aliasing.spatial_sample_count = spatial_aa
        anti_aliasing.temporal_sample_count = temporal_aa
    except Exception:
        pass

    unreal.log(f"[MHPD Batch Render] Configured MRQ job: sequence={seq_str}, map={map_str}, output={output_frame_dir} ({actual_res_x}x{actual_res_y}, {warm_up} warm-up frames)")
    return subsystem, job


class _RenderQueueManager:
    """Manages active rendering delegate and sequential batch queue."""
    def __init__(self):
        self.queue = []
        self.is_rendering = False
        self.active_job = None
        self.active_callback = None
        self.active_executor = None
        self.active_mrq_subsystem = None
        self.cooldown_until = 0.0
        self.cooldown_handle = None

    def add_job(
        self,
        sequence_path: str,
        output_dir: str,
        res_x: int = 1920,
        res_y: int = 1080,
        fps: int = 30,
        quality_preset: int = 1,
        shot_preset: str = "",
        camera_angle: str = "front",
        focal_length: float = 0.0,
        preserve_existing_camera: bool = False,
        filename_template: str = "{take}_{performer}_{shot}_{angle}_{lens}_{version}",
        look: str = "clean",
        look_intensity: float = 1.0,
    ):
        look, look_intensity = _validated_look(look, look_intensity)
        self.queue.append({
            "sequence_path": sequence_path,
            "output_dir": output_dir,
            "res_x": res_x,
            "res_y": res_y,
            "fps": fps,
            "quality_preset": quality_preset,
            "shot_preset": shot_preset,
            "camera_angle": camera_angle,
            "focal_length": focal_length,
            "preserve_existing_camera": preserve_existing_camera,
            "filename_template": filename_template,
            "look": look,
            "look_intensity": look_intensity,
        })
        self.process_next()

    def process_next(self):
        if self.is_rendering or self.cooldown_handle is not None:
            return
        if not self.queue:
            unreal.log("[MHPD Batch Render] ✓ All pending render jobs completed.")
            return

        self.active_job = self.queue.pop(0)
        self.is_rendering = True

        seq_path = self.active_job["sequence_path"]
        target_out_dir = self.active_job["output_dir"]
        res_x = self.active_job["res_x"]
        res_y = self.active_job["res_y"]
        fps = self.active_job["fps"]
        quality_preset = self.active_job.get("quality_preset", 1)

        seq_asset = unreal.load_asset(seq_path)
        if not seq_asset:
            unreal.log_error(f"[MHPD Batch Render] Could not load Level Sequence: {seq_path}")
            self.is_rendering = False
            self.process_next()
            return

        # 1. Ensure Camera Cut track exists so capture viewports focus on the MetaHuman face
        try:
            if self.active_job.get("preserve_existing_camera", False):
                unreal.log(
                    "[MHPD Batch Render] Preserving the accepted Sequencer camera; dropdowns are not applied."
                )
            elif not ensure_camera_cut_track(
                    seq_asset,
                    shot_preset=self.active_job.get("shot_preset", ""),
                    camera_angle=self.active_job.get("camera_angle", "front"),
                    focal_length=self.active_job.get("focal_length", 0.0)):
                raise RuntimeError("Could not generate the render camera.")
            _render_camera_binding(seq_asset)
            apply_camera_look_to_sequence(seq_path, self.active_job.get("look", "clean"),
                                          self.active_job.get("look_intensity", 1.0))
        except Exception:
            self.is_rendering = False
            self.active_job = None
            raise

        # 2. Extract dialogue audio track source
        audio_path = get_audio_source_from_sequence(seq_asset)

        take_name = seq_asset.get_name()
        if take_name.startswith("LS_"):
            take_name = take_name[3:]

        mh_actor = _find_metahuman_actor(unreal.get_editor_subsystem(unreal.EditorActorSubsystem))
        performer_name = mh_actor.get_actor_label() if mh_actor else "MetaHuman"
        focal_length = float(self.active_job.get("focal_length", 0.0) or 0.0)
        lens_name = f"{focal_length:g}mm" if focal_length > 0.0 else "Auto"
        camera_tokens = _manual_camera_output_tokens(seq_asset) if self.active_job.get("preserve_existing_camera") else {
            "shot": self.active_job.get("shot_preset", "shot"),
            "angle": self.active_job.get("camera_angle", "front"), "lens": lens_name,
        }
        final_mp4 = _resolve_output_path(
            target_out_dir,
            self.active_job.get("filename_template", "{take}_{version}"),
            {
                "take": take_name,
                "performer": performer_name,
                "look": self.active_job.get("look", "clean"),
                **camera_tokens,
            },
        )
        output_stem = Path(final_mp4).stem
        temp_frames = os.path.join(target_out_dir, f"_temp_frames_{output_stem}")
        self.active_job["temp_frames"] = temp_frames
        self.active_job["final_mp4"] = final_mp4
        self.active_job["take_name"] = take_name
        self.active_job["audio_path"] = audio_path

        if os.path.isdir(temp_frames):
            shutil.rmtree(temp_frames)
        os.makedirs(temp_frames, exist_ok=True)

        unreal.log(f"[MHPD Batch Render] >>> Starting MRQ render for '{take_name}' (Quality Preset: {quality_preset})...")
        try:
            self.active_mrq_subsystem, _ = create_mrq_job(
                seq_path, temp_frames, res_x=res_x, res_y=res_y, fps=fps, quality_preset=quality_preset
            )
            self.active_executor = unreal.MoviePipelinePIEExecutor(self.active_mrq_subsystem)
            self.active_executor.on_executor_finished_delegate.add_callable_unique(self._on_mrq_finished)
            self.active_mrq_subsystem.render_queue_with_executor_instance(self.active_executor)
        except Exception as e:
            unreal.log_error(f"[MHPD Batch Render] Exception starting MRQ: {e}")
            self.is_rendering = False
            self.active_executor = None
            self.active_mrq_subsystem = None
            self.process_next()

    def _begin_next_job_with_cooldown(self, completed_quality: int):
        """Leaves the editor responsive while allowing hardware to cool between heavy jobs."""
        cooldown_seconds = 15.0 if completed_quality == 2 and self.queue else 0.0
        if cooldown_seconds <= 0.0:
            self.process_next()
            return

        self.cooldown_until = time.monotonic() + cooldown_seconds
        unreal.log(
            f"[MHPD Batch Render] Cooling down for {cooldown_seconds:.0f}s before the next "
            f"Cinematic Master job ({len(self.queue)} remaining)."
        )
        self.cooldown_handle = unreal.register_slate_post_tick_callback(self._on_cooldown_tick)

    def _on_cooldown_tick(self, delta_time):
        if time.monotonic() < self.cooldown_until:
            return
        if self.cooldown_handle is not None:
            unreal.unregister_slate_post_tick_callback(self.cooldown_handle)
            self.cooldown_handle = None
        self.cooldown_until = 0.0
        self.process_next()

    def _on_mrq_finished(self, executor, success: bool):
        unreal.log(f"[MHPD Batch Render] MRQ finished: success={success}")
        completed_quality = self.active_job.get("quality_preset", 1) if self.active_job else 1
        try:
            if self.active_job:
                temp_frames = self.active_job["temp_frames"]
                final_mp4 = self.active_job["final_mp4"]
                fps = self.active_job["fps"]
                take_name = self.active_job["take_name"]
                audio_path = self.active_job.get("audio_path")

                if success and os.path.exists(temp_frames):
                    compile_ok = compile_frames_to_mp4(temp_frames, final_mp4, audio_path=audio_path, fps=fps)
                    if compile_ok:
                        unreal.log(f"[MHPD Batch Render] ✓ Rendered take '{take_name}' -> {final_mp4}")
                    else:
                        unreal.log_error(f"[MHPD Batch Render] ❌ Failed to encode MP4 for '{take_name}'")
                elif success:
                    unreal.log_warning(f"[MHPD Batch Render] Temp frames directory not found: {temp_frames}")
                else:
                    unreal.log_error(f"[MHPD Batch Render] MRQ failed for '{take_name}'; frames were not encoded.")
        except Exception as e:
            unreal.log_error(f"[MHPD Batch Render] Error during post-capture encoding: {e}")
        finally:
            self.is_rendering = False
            self.active_job = None
            self.active_callback = None
            self.active_executor = None
            self.active_mrq_subsystem = None
            self._begin_next_job_with_cooldown(completed_quality)


# Global persistent manager instance
# UI handlers reload this module. Keep an in-flight executor/queue reachable so a
# second click cannot start an overlapping PIE render with a fresh manager.
_MANAGER = globals().get("_MANAGER") or _RenderQueueManager()


def render_take(
    sequence_path: str,
    output_dir: str | None = None,
    res_x: int = 1920,
    res_y: int = 1080,
    fps: int = 30,
    quality_preset: int = 1,
    shot_preset: str = "",
    camera_angle: str = "front",
    focal_length: float = 0.0,
    preserve_existing_camera: bool = False,
    filename_template: str = "{take}_{performer}_{shot}_{angle}_{lens}_{version}",
    look: str = "clean",
    look_intensity: float = 1.0,
):
    """Queues a single Level Sequence take to render to MP4 with specified quality preset."""
    if _MANAGER.is_rendering:
        raise RuntimeError("A render is already running. Wait for it to finish or cancel it before submitting another.")
    target_out_dir = str(output_dir or DEFAULT_OUTPUT_DIR)
    os.makedirs(target_out_dir, exist_ok=True)
    _MANAGER.add_job(
        sequence_path,
        target_out_dir,
        res_x=res_x,
        res_y=res_y,
        fps=fps,
        quality_preset=quality_preset,
        shot_preset=shot_preset,
        camera_angle=camera_angle,
        focal_length=focal_length,
        preserve_existing_camera=preserve_existing_camera,
        filename_template=filename_template,
        look=look,
        look_intensity=look_intensity,
    )


def get_all_takes_in_folder(take_dir: str = "/Game/MHPD/Take_001") -> list[str]:
    """Retrieves all Level Sequence asset paths in the specified package folder."""
    asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
    filter = unreal.ARFilter(
        package_paths=[take_dir],
        class_names=["LevelSequence"],
        recursive_paths=False
    )
    assets = asset_registry.get_assets(filter)
    
    # Sort chronologically by package file creation timestamp
    def get_asset_ctime(asset_data):
        pkg_name = str(asset_data.package_name)
        if pkg_name.startswith("/Game/"):
            content_dir = unreal.Paths.project_content_dir()
            filename = os.path.join(content_dir, pkg_name[6:]) + ".uasset"
            try:
                return os.path.getctime(filename)
            except OSError:
                return 0.0
        return 0.0

    sorted_assets = sorted(assets, key=get_asset_ctime)
    return [f"{a.package_name}.{a.asset_name}" for a in sorted_assets]


def render_all_takes(
    take_dir: str = "/Game/MHPD/Take_001",
    output_dir: str | None = None,
    res_x: int = 1920,
    res_y: int = 1080,
    fps: int = 30,
    quality_preset: int = 1,
    shot_preset: str = "",
    camera_angle: str = "front",
    focal_length: float = 0.0,
    preserve_existing_camera: bool = False,
    filename_template: str = "{take}_{performer}_{shot}_{angle}_{lens}_{version}",
    preserved_camera_sequences: list[str] | None = None,
    require_saved_cameras: bool = False,
    look: str = "clean",
    look_intensity: float = 1.0,
):
    """Queues all takes in the folder sequentially for batch rendering with specified quality preset."""
    target_out_dir = str(output_dir or DEFAULT_OUTPUT_DIR)
    look, look_intensity = _validated_look(look, look_intensity)
    os.makedirs(target_out_dir, exist_ok=True)
    
    take_paths = get_all_takes_in_folder(take_dir)
    authored_paths = {path.split('.', 1)[0] for path in (preserved_camera_sequences or [])}
    if require_saved_cameras:
        missing = [path for path in take_paths if not preserve_existing_camera and path.split('.', 1)[0] not in authored_paths]
        if missing:
            raise RuntimeError("Manual batch blocked: save Manual Framing for every take first, or switch to Preset. Missing: "
                               + ", ".join(missing))
    unreal.log(f"[MHPD Batch Render] Found {len(take_paths)} takes in '{take_dir}' to queue.")
    for seq_path in take_paths:
        _MANAGER.add_job(
            seq_path,
            target_out_dir,
            res_x=res_x,
            res_y=res_y,
            fps=fps,
            quality_preset=quality_preset,
            shot_preset=shot_preset,
            camera_angle=camera_angle,
            focal_length=focal_length,
            preserve_existing_camera=preserve_existing_camera or seq_path.split('.', 1)[0] in authored_paths,
            filename_template=filename_template,
            look=look,
            look_intensity=look_intensity,
        )


if __name__ == "__main__":
    # Command line invocation
    import argparse
    parser = argparse.ArgumentParser(description="MHPD Batch Take Video Renderer")
    parser.add_argument("--take", type=str, help="Specific sequence asset path to render")
    parser.add_argument("--take_dir", type=str, default="/Game/MHPD/Take_001", help="Folder of takes to batch render")
    parser.add_argument("--output_dir", type=str, default=str(DEFAULT_OUTPUT_DIR), help="Output folder for MP4 videos")
    parser.add_argument("--quality", type=int, default=1, choices=[0, 1, 2], help="Render quality (0=Draft, 1=Production, 2=Cinematic)")
    parser.add_argument("--all", action="store_true", help="Batch render all takes in take_dir")

    args = parser.parse_args()
    if args.take:
        render_take(args.take, output_dir=args.output_dir, quality_preset=args.quality)
    elif args.all:
        render_all_takes(take_dir=args.take_dir, output_dir=args.output_dir, quality_preset=args.quality)
    else:
        render_all_takes(take_dir=args.take_dir, output_dir=args.output_dir, quality_preset=args.quality)
