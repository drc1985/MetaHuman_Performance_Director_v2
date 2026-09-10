using UnrealBuildTool;

public class MetaHumanPerformanceDirector : ModuleRules
{
    public MetaHumanPerformanceDirector(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(
            new[]
            {
                "Core",
                "CoreUObject",
                "EditorSubsystem",
                "Engine",
                "Json",
                "JsonUtilities",
                "LevelSequence",
                "MovieScene",
                "MovieSceneTracks",
                "AssetRegistry"
            }
        );

        PrivateDependencyModuleNames.AddRange(
            new[]
            {
                "Slate",
                "SlateCore",
                "ToolMenus",
                "UnrealEd",
                "ControlRig",
                "ControlRigEditor",
                "AnimationCore",
                "InputCore",
                "DesktopPlatform",
                "PythonScriptPlugin",
                "AssetTools"
            }
        );
    }
}