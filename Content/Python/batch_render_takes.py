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
from pathlib import Path

# Resolve default output directory
DEFAULT_PROJECT_DIR = Path(unreal.Paths.project_dir()).resolve()
# Fallback to repo Test/Review_v0.3.0 folder
REPO_REVIEW_DIR = Path(r"e:\DavidCobbinsGlobal\Software\MetaHumanPerformanceDirector\MetaHumanPerformanceDirector\Test\Review_v0.3.0")
DEFAULT_OUTPUT_DIR = REPO_REVIEW_DIR if REPO_REVIEW_DIR.exists() else (DEFAULT_PROJECT_DIR / "Saved" / "VideoCaptures")

DEFAULT_RENDER_MAP = "/Game/DevBuild"
REVIEW_CAMERA_PULLBACK = 1.65
REVIEW_CAMERA_HEIGHT_OFFSET = -18.0

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


def get_optimal_camera_transform(pullback: float | None = None, height_offset: float | None = None) -> tuple[unreal.Vector, unreal.Rotator]:
    """Calculates the optimal camera transform targeting the MetaHuman face, respecting framing pullback and height."""
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)

    actual_pullback = REVIEW_CAMERA_PULLBACK if pullback is None else float(pullback)
    actual_height_offset = REVIEW_CAMERA_HEIGHT_OFFSET if height_offset is None else float(height_offset)

    mh_actor = None
    if actor_subsystem:
        for a in actor_subsystem.get_all_level_actors():
            name = a.get_name()
            cls_name = a.get_class().get_name()
            if "MH_Demo" in name or "MetaHuman" in cls_name or "BP_MH_" in cls_name:
                mh_actor = a
                break

    # Verified framing in DevBuild:
    # MH actor at (36820.0, -7930.0, 10.0), face at Z = 168.7.
    # Camera at (36740.2, -8034.4, 168.7), Pitch=4.2, Yaw=54.6, Roll=0.0 directly faces character (131cm distance).
    DEFAULT_CAM_LOC = unreal.Vector(36740.2, -8034.4, 168.7)
    DEFAULT_CAM_ROT = unreal.Rotator(pitch=4.2, yaw=54.6, roll=0.0)

    # 1. Preserve a nearby viewport camera's angle, but widen its framing around
    # the face anchor so the complete head and neck remain visible during turns.
    if editor_subsystem and mh_actor:
        cam_info = editor_subsystem.get_level_viewport_camera_info()
        if cam_info:
            vp_loc, vp_rot = cam_info
            mh_loc = mh_actor.get_actor_location()
            face_anchor = unreal.Vector(mh_loc.x, mh_loc.y, mh_loc.z + 158.7)
            face_offset = vp_loc - face_anchor
            dist = face_offset.length()
            if 50.0 < dist < 600.0:
                cam_loc = face_anchor + (face_offset * actual_pullback)
                cam_loc.z += actual_height_offset
                unreal.log(
                    f"[MHPD Batch Render] Widened active viewport framing "
                    f"from {dist:.1f}cm to {(cam_loc - face_anchor).length():.1f}cm: "
                    f"{cam_loc}, {vp_rot}"
                )
                return cam_loc, vp_rot

    # 2. Derive a wider MCU from the MetaHuman face position if no usable
    # viewport framing exists. The previous 131cm distance cropped head/neck.
    if mh_actor:
        mh_loc = mh_actor.get_actor_location()
        cam_loc = unreal.Vector(
            mh_loc.x - (79.8 * actual_pullback),
            mh_loc.y - (104.4 * actual_pullback),
            mh_loc.z + 158.7 + actual_height_offset,
        )
        unreal.log(f"[MHPD Batch Render] Derived wide MCU camera from MetaHuman at {mh_loc} -> {cam_loc}")
        return cam_loc, DEFAULT_CAM_ROT

    # 3. Fallback to verified DevBuild constants
    default_face_anchor = unreal.Vector(36820.0, -7930.0, 168.7)
    default_offset = DEFAULT_CAM_LOC - default_face_anchor
    wide_default_loc = default_face_anchor + (default_offset * actual_pullback)
    wide_default_loc.z += actual_height_offset
    unreal.log(f"[MHPD Batch Render] Using default wide MCU framing -> {wide_default_loc}")
    return wide_default_loc, DEFAULT_CAM_ROT


def ensure_camera_cut_track(seq_asset, framing_scale: float | None = None) -> bool:
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

    scale_val = 0.50 if framing_scale is None else float(framing_scale)
    if scale_val <= 0.20:
        target_focal_length = 55.0
        scale_pullback = 1.30
        scale_height_offset = -12.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Close-Up (55mm, pullback 1.30, height -12cm)")
    elif scale_val <= 0.40:
        target_focal_length = 52.0
        scale_pullback = 1.45
        scale_height_offset = -14.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Medium Close-Up (52mm, pullback 1.45, height -14cm)")
    elif scale_val >= 0.70:
        target_focal_length = 35.0
        scale_pullback = 2.00
        scale_height_offset = -20.0
        unreal.log(f"[MHPD Batch Render] Framing scale {scale_val:.2f} -> Theatrical Wide (35mm, pullback 2.00, height -20cm)")
    else:
        target_focal_length = 50.0
        scale_pullback = REVIEW_CAMERA_PULLBACK
        scale_height_offset = REVIEW_CAMERA_HEIGHT_OFFSET

    # 4. Determine camera location and rotation
    cam_loc, cam_rot = get_optimal_camera_transform(pullback=scale_pullback, height_offset=scale_height_offset)

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

    # 7. Destroy temporary level actor — sequence asset now owns the spawnable template
    actor_subsystem.destroy_actor(temp_cam)

    if not cam_binding or not cam_binding.is_valid():
        unreal.log_error(f"[MHPD Batch Render] Failed to create spawnable camera binding in '{seq_asset.get_name()}'.")
        return False

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
        unreal.log_warning(f"[MHPD Batch Render] Could not configure spawn track for spawnable camera: {e}")

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
        unreal.log_warning(f"[MHPD Batch Render] Could not configure transform track for spawnable camera: {e}")

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
    except Exception as e:
        unreal.log_warning(f"[MHPD Batch Render] Could not save sequence asset: {e}")

    # 10. Refresh Sequencer UI if open
    try:
        unreal.LevelSequenceEditorBlueprintLibrary.refresh_current_level_sequence()
    except Exception:
        pass

    return True


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
    """Returns the loaded editor map when it is a saved asset, otherwise DevBuild."""
    try:
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        world = editor_subsystem.get_editor_world() if editor_subsystem else None
        if world:
            package_path = str(world.get_outermost().get_name())
            if package_path.startswith("/Game/"):
                return package_path
    except Exception as e:
        unreal.log_warning(f"[MHPD Batch Render] Could not resolve current editor map: {e}")
    return DEFAULT_RENDER_MAP


def create_mrq_job(sequence_path: str, output_frame_dir: str, res_x: int = 1920,
                   res_y: int = 1080, fps: int = 30, quality_preset: int = 1):
    """
    Creates one MRQ job that evaluates the sequence and its camera cuts in PIE.
    Quality Presets (§2):
      0 = Draft Preview (1080p, 10 warm-up frames)
      1 = Production Hero (1440p/QHD, 48 warm-up frames for Lumen GI & hair groom settling, 4x/2x AA)
      2 = Cinematic Master (4K UHD, 64 warm-up frames, 8x/4x AA)
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
        warm_up = 64
        spatial_aa, temporal_aa = 8, 4
        unreal.log("[MHPD Batch Render] Applying 'Cinematic Master' preset (4K UHD, 64 warm-up frames, 8x/4x AA)")
    else:  # ProductionHero (Default 1)
        actual_res_x, actual_res_y = 2560, 1440
        warm_up = 48
        spatial_aa, temporal_aa = 4, 2
        unreal.log("[MHPD Batch Render] Applying 'Production Hero' preset (1440p QHD, 48 warm-up frames, 4x/2x AA)")

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

    def add_job(self, sequence_path: str, output_dir: str, res_x: int = 1920, res_y: int = 1080, fps: int = 30, quality_preset: int = 1):
        self.queue.append({
            "sequence_path": sequence_path,
            "output_dir": output_dir,
            "res_x": res_x,
            "res_y": res_y,
            "fps": fps,
            "quality_preset": quality_preset
        })
        self.process_next()

    def process_next(self):
        if self.is_rendering:
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
        ensure_camera_cut_track(seq_asset)

        # 2. Extract dialogue audio track source
        audio_path = get_audio_source_from_sequence(seq_asset)

        take_name = seq_asset.get_name()
        if take_name.startswith("LS_"):
            take_name = take_name[3:]

        temp_frames = os.path.join(target_out_dir, f"_temp_frames_{take_name}")
        final_mp4 = os.path.join(target_out_dir, f"{take_name}.mp4")
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

    def _on_mrq_finished(self, executor, success: bool):
        unreal.log(f"[MHPD Batch Render] MRQ finished: success={success}")
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
            self.process_next()


# Global persistent manager instance
_MANAGER = _RenderQueueManager()


def render_take(sequence_path: str, output_dir: str | None = None, res_x: int = 1920, res_y: int = 1080, fps: int = 30, quality_preset: int = 1):
    """Queues a single Level Sequence take to render to MP4 with specified quality preset."""
    target_out_dir = str(output_dir or DEFAULT_OUTPUT_DIR)
    os.makedirs(target_out_dir, exist_ok=True)
    _MANAGER.add_job(sequence_path, target_out_dir, res_x=res_x, res_y=res_y, fps=fps, quality_preset=quality_preset)


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


def render_all_takes(take_dir: str = "/Game/MHPD/Take_001", output_dir: str | None = None, res_x: int = 1920, res_y: int = 1080, fps: int = 30, quality_preset: int = 1):
    """Queues all takes in the folder sequentially for batch rendering with specified quality preset."""
    target_out_dir = str(output_dir or DEFAULT_OUTPUT_DIR)
    os.makedirs(target_out_dir, exist_ok=True)
    
    take_paths = get_all_takes_in_folder(take_dir)
    unreal.log(f"[MHPD Batch Render] Found {len(take_paths)} takes in '{take_dir}' to queue.")
    for seq_path in take_paths:
        _MANAGER.add_job(seq_path, target_out_dir, res_x=res_x, res_y=res_y, fps=fps, quality_preset=quality_preset)


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
