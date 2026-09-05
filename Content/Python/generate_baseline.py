import unreal
import os

# ==============================================================================
# MetaHuman Performance Director - Baseline Generator
# ==============================================================================
# This script feeds an audio file into Epic's MetaHuman Animator (MHA) to bake
# out a baseline facial performance (lip-sync + emotion).
#
# Can be called from the C++ plugin UI (with keyword args) or directly from the
# Unreal Python console (uses the defaults below).
# ==============================================================================

# ----------------- CONFIGURATION (used when called from Python console) ------
AUDIO_FILE_PATH = r"E:\DavidCobbinsGlobal\Software\MetaHumanPerformanceDirector\outputs\fearful_female_american_voiceover.wav"
OUTPUT_DIR = "/Game/MHPD/BaselineTake"
# -----------------------------------------------------------------------------


def import_audio(file_path, destination_path):
    """Imports a .wav file from disk into Unreal Engine as a SoundWave asset."""
    unreal.log(f"Importing audio from: {file_path}")

    task = unreal.AssetImportTask()
    task.filename = file_path
    task.destination_path = destination_path
    task.destination_name = "DialogueAudio_Base"
    task.replace_existing = True
    task.automated = True
    task.save = True

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([task])

    return f"{destination_path}/DialogueAudio_Base.DialogueAudio_Base"


def generate_mha_performance(audio_asset_path, output_dir):
    """Uses the UE5.6+ MetaHumanPerformance asset API to generate an Audio-to-Face AnimSequence."""
    unreal.log("Loading audio asset for MHA processing...")
    sound_wave_asset = unreal.EditorAssetLibrary.load_asset(audio_asset_path)

    if not sound_wave_asset:
        unreal.log_error(f"Failed to load Audio Asset at {audio_asset_path}")
        return None

    unreal.log("Creating MetaHuman Performance Asset...")
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    performance_asset = asset_tools.create_asset(
        asset_name="AudioPerformance_Base",
        package_path=output_dir,
        asset_class=unreal.MetaHumanPerformance,
        factory=unreal.MetaHumanPerformanceFactoryNew()
    )

    if not performance_asset:
        unreal.log_error("Failed to create MetaHuman Performance asset.")
        return None

    # Configure for audio input
    performance_asset.set_editor_property("input_type", unreal.DataInputType.AUDIO)
    performance_asset.set_editor_property("audio", sound_wave_asset)

    # Configure mood
    solve_overrides = unreal.AudioDrivenAnimationSolveOverrides()
    solve_overrides.mood = unreal.AudioDrivenAnimationMood.AUTO_DETECT
    solve_overrides.mood_intensity = 1.0
    performance_asset.set_editor_property("audio_driven_animation_solve_overrides", solve_overrides)

    # Process (blocking)
    unreal.log("Processing MetaHuman Audio-to-Face pipeline (this may take a moment)...")
    performance_asset.set_blocking_processing(True)
    start_error = performance_asset.start_pipeline()

    if start_error != unreal.StartPipelineErrorType.NONE:
        unreal.log_error(f"Error starting MH pipeline: {start_error}")
        return None

    # Export to AnimSequence targeting the common MetaHuman face skeleton
    unreal.log("Exporting Animation Sequence...")
    export_settings = unreal.MetaHumanPerformanceExportAnimationSettings()
    export_settings.show_export_dialog = False
    export_settings.package_path = output_dir
    export_settings.asset_name = "Anim_Baseline_Face"

    target_skeleton = unreal.EditorAssetLibrary.load_asset(
        '/Game/MetaHumans/Common/Face/Face_Archetype_Skeleton.Face_Archetype_Skeleton'
    )
    if not target_skeleton:
        unreal.log_error("Failed to find Face_Archetype_Skeleton. Is MetaHuman plugin installed?")
        return None

    export_settings.target_skeleton_or_skeletal_mesh = target_skeleton
    # Head movement OFF: the face anim must not carry its own neck/head bone
    # rotation. The Body component owns the neck — the Face AnimBP copies the
    # body pose every frame. Two head-motion sources fight and cause seams.
    export_settings.enable_head_movement = False
    export_settings.export_range = unreal.PerformanceExportRange.PROCESSING_RANGE

    anim_sequence = unreal.MetaHumanPerformanceExportUtils.export_animation_sequence(
        performance_asset, export_settings
    )

    if anim_sequence:
        settle_mouth_curves(anim_sequence)
        unreal.log(f"SUCCESS: Exported Anim Sequence '{anim_sequence.get_name()}' to {output_dir}")
    else:
        unreal.log_error("Failed to export Anim Sequence.")

    return anim_sequence


def settle_mouth_curves(anim_sequence, settle_duration=0.40, lead_in_duration=0.20):
    """
    Ensures ALL mouth, jaw, and lip RigLogic curves:
    1. Start at 0.0 at frame 0 (t=0.0) with a closed mouth, smoothly easing into speech.
    2. Settle smoothly to 0.0 at the end of the take, holding closed rest pose.
    """
    if not anim_sequence:
        return
    seq_length = unreal.AnimationLibrary.get_sequence_length(anim_sequence)
    if seq_length <= (settle_duration + lead_in_duration):
        return

    settle_start = max(0.0, seq_length - settle_duration)
    all_curves = [str(n) for n in unreal.AnimationLibrary.get_animation_curve_names(
        anim_sequence, unreal.RawCurveTrackTypes.RCT_FLOAT
    )]

    # Targets ANY curve affecting mouth, jaw, lips, or chin
    target_keywords = ("mouth", "jaw", "lip", "chin")

    for curve_name in all_curves:
        cl = curve_name.lower()
        if any(k in cl for k in target_keywords):
            times, values = unreal.AnimationLibrary.get_float_keys(anim_sequence, curve_name)
            if not times:
                continue

            raw_keys = [(float(t), float(v)) for t, v in zip(times, values)]
            raw_keys.sort(key=lambda kv: kv[0])

            # Keep keys between lead-in and settle
            middle_keys = [(t, v) for t, v in raw_keys if t >= lead_in_duration and t < settle_start]

            # Build lead-in keys (closed mouth at t=0, easing in)
            lead_in_val = 0.0
            for t, v in raw_keys:
                if t >= lead_in_duration:
                    lead_in_val = v
                    break

            new_keys = [(0.0, 0.0)]
            if abs(lead_in_val) > 0.005:
                new_keys.append((lead_in_duration * 0.5, lead_in_val * 0.35))
            new_keys.extend(middle_keys)

            # Sample value at settle_start
            val_at_settle = 0.0
            for t, v in raw_keys:
                if t <= settle_start:
                    val_at_settle = v

            if abs(val_at_settle) > 0.005:
                mid_time = settle_start + settle_duration * 0.45
                new_keys.append((mid_time, val_at_settle * 0.30))
                pre_end = settle_start + settle_duration * 0.85
                new_keys.append((pre_end, 0.0))

            # Flat zero hold at end of sequence
            new_keys.append((seq_length, 0.0))
            new_keys.sort(key=lambda kv: kv[0])

            unreal.AnimationLibrary.remove_curve(anim_sequence, curve_name)
            unreal.AnimationLibrary.add_curve(anim_sequence, curve_name)
            unreal.AnimationLibrary.add_float_curve_keys(
                anim_sequence,
                curve_name,
                [k[0] for k in new_keys],
                [k[1] for k in new_keys]
            )

    unreal.EditorAssetLibrary.save_loaded_asset(anim_sequence)
    unreal.log(f"MHPD: Successfully settled start and end mouth/jaw curves on '{anim_sequence.get_name()}'")


def main(audio_path=None, output_dir=None):
    """
    Main entry point. Accepts optional keyword arguments so it can be driven
    by the C++ plugin UI. Falls back to the module-level constants when called
    directly from the Python console.

    Args:
        audio_path (str): Absolute path to the .wav file on disk.
        output_dir (str): UE content path for the output assets, e.g. '/Game/MHPD/MyTake'.
    """
    audio_path = audio_path or AUDIO_FILE_PATH
    output_dir = output_dir or OUTPUT_DIR

    if not os.path.exists(audio_path):
        unreal.log_error(f"Audio file not found at: {audio_path}")
        return False

    # 1. Import the audio into Unreal
    imported_audio_path = import_audio(audio_path, output_dir)

    # 2. Process with MetaHuman Animator and export AnimSequence
    anim_sequence = generate_mha_performance(imported_audio_path, output_dir)

    if anim_sequence:
        unreal.log("MHPD: Baseline generation complete.")
        return True
    else:
        unreal.log_error("MHPD: Baseline generation failed.")
        return False


if __name__ == "__main__":
    main()
