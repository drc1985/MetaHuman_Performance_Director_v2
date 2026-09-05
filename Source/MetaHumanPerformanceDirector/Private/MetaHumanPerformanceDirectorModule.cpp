// Copyright MetaHuman Performance Director. All Rights Reserved.

#include "Modules/ModuleManager.h"

#include "Editor.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/Selection.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "Channels/MovieSceneChannelProxy.h"
#include "Channels/MovieSceneDoubleChannel.h"
#include "LevelSequence.h"
#include "LevelSequenceActor.h"
#include "Subsystems/AssetEditorSubsystem.h"
#include "MovieScene.h"
#include "MovieScenePossessable.h"
#include "ControlRig.h"
#include "Rigs/RigHierarchy.h"
#include "ControlRigObjectBinding.h"
#include "Sequencer/MovieSceneControlRigParameterSection.h"
#include "Sequencer/MovieSceneControlRigParameterTrack.h"
#include "Sections/MovieScene3DTransformSection.h"
#include "Tracks/MovieScene3DTransformTrack.h"
#include "Tracks/MovieSceneAudioTrack.h"
#include "Sections/MovieSceneAudioSection.h"
#include "Tracks/MovieSceneSkeletalAnimationTrack.h"
#include "Sections/MovieSceneSkeletalAnimationSection.h"
#include "UObject/Package.h"
#include "Editor/EditorEngine.h"
#include "LevelEditorViewport.h"
#include "GameFramework/Actor.h"
#include "Framework/Commands/UIAction.h"
#include "Framework/Docking/TabManager.h"
#include "MHPDPerformanceDirectorSubsystem.h"
#include "Styling/AppStyle.h"
#include "ToolMenus.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SCompoundWidget.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SEditableTextBox.h"
#include "Widgets/Input/SMultiLineEditableTextBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SSeparator.h"
#include "Widgets/Layout/SScrollBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Misc/InteractiveProcess.h"
#include "Async/Async.h"
#include "Widgets/Input/SComboBox.h"
#include "DesktopPlatformModule.h"
#include "IDesktopPlatform.h"
#include "IPythonScriptPlugin.h"
#include "Sound/SoundWave.h"
#include "Animation/AnimSequence.h"
#include "Animation/Skeleton.h"
#include "Animation/AnimData/IAnimationDataModel.h"
#include "Animation/AnimData/IAnimationDataController.h"
#include "FileHelpers.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"

#define LOCTEXT_NAMESPACE "FMetaHumanPerformanceDirectorModule"

namespace
{
    static const FName MHPDTabName(TEXT("MetaHumanPerformanceDirector"));

    bool IsChecked(const TSharedPtr<SCheckBox>& CheckBox)
    {
        return CheckBox.IsValid() && CheckBox->GetCheckedState() == ECheckBoxState::Checked;
    }

    FString ChannelToString(EMHPDPerformanceChannel Channel)
    {
        switch (Channel)
        {
            case EMHPDPerformanceChannel::FacialExpression: return TEXT("Facial expression");
            case EMHPDPerformanceChannel::Gaze:             return TEXT("Eye contact / gaze");
            case EMHPDPerformanceChannel::HeadMovement:     return TEXT("Head movement");
            case EMHPDPerformanceChannel::Gesture:          return TEXT("Gesture");
            case EMHPDPerformanceChannel::BodyPosture:      return TEXT("Body posture");
            case EMHPDPerformanceChannel::ReactionTiming:   return TEXT("Reaction timing");
            case EMHPDPerformanceChannel::Pauses:           return TEXT("Pauses");
            case EMHPDPerformanceChannel::VoiceDelivery:    return TEXT("Voice delivery");
            default:                                        return TEXT("Unknown channel");
        }
    }

    FString MakeTakeToken(FString Value)
    {
        Value = Value.ToLower();
        Value.ReplaceInline(TEXT(" "),  TEXT("_"));
        Value.ReplaceInline(TEXT("/"),  TEXT("_"));
        Value.ReplaceInline(TEXT("\\"), TEXT("_"));
        Value.ReplaceInline(TEXT(":"),  TEXT("_"));
        Value.ReplaceInline(TEXT("."),  TEXT("_"));
        Value.ReplaceInline(TEXT(","),  TEXT(""));
        Value.ReplaceInline(TEXT("'"),  TEXT(""));
        Value.ReplaceInline(TEXT("\""), TEXT(""));
        return Value.Left(36);
    }

    FString MakeAssetSafeName(FString Value)
    {
        Value.ReplaceInline(TEXT(" "),  TEXT("_"));
        Value.ReplaceInline(TEXT("/"),  TEXT("_"));
        Value.ReplaceInline(TEXT("\\"), TEXT("_"));
        Value.ReplaceInline(TEXT(":"),  TEXT("_"));
        Value.ReplaceInline(TEXT("."),  TEXT("_"));
        Value.ReplaceInline(TEXT("("),  TEXT("_"));
        Value.ReplaceInline(TEXT(")"),  TEXT("_"));
        Value.ReplaceInline(TEXT("["),  TEXT("_"));
        Value.ReplaceInline(TEXT("]"),  TEXT("_"));
        Value.ReplaceInline(TEXT("{"),  TEXT("_"));
        Value.ReplaceInline(TEXT("}"),  TEXT("_"));
        Value.ReplaceInline(TEXT(","),  TEXT(""));
        Value.ReplaceInline(TEXT("'"),  TEXT(""));
        Value.ReplaceInline(TEXT("\""), TEXT(""));
        Value.ReplaceInline(TEXT("?"),  TEXT(""));
        Value.ReplaceInline(TEXT("!"),  TEXT(""));
        Value.ReplaceInline(TEXT("@"),  TEXT(""));
        Value.ReplaceInline(TEXT("#"),  TEXT(""));
        Value.ReplaceInline(TEXT("$"),  TEXT(""));
        Value.ReplaceInline(TEXT("%"),  TEXT(""));
        Value.ReplaceInline(TEXT("^"),  TEXT(""));
        Value.ReplaceInline(TEXT("&"),  TEXT(""));
        Value.ReplaceInline(TEXT("*"),  TEXT(""));
        Value.ReplaceInline(TEXT("+"),  TEXT(""));
        Value.ReplaceInline(TEXT("="),  TEXT(""));
        Value.ReplaceInline(TEXT(";"),  TEXT(""));
        return Value;
    }

    static const FName BriefGazeBreakBehaviorId(TEXT("brief_gaze_break_before_answer"));
    static const FName CloseEyesBehaviorId(TEXT("close_eyes_before_answer"));

    bool TryGetGazeOrEyeInstruction(const FMHPDPerformancePlan& Plan, FMHPDChannelInstruction& OutInstruction)
    {
        for (const FMHPDChannelInstruction& Instruction : Plan.Instructions)
        {
            if (Instruction.BehaviorId == CloseEyesBehaviorId && !Instruction.bPreserveOriginal && Instruction.Weight > 0.0f)
            {
                OutInstruction = Instruction;
                return true;
            }
        }
        for (const FMHPDChannelInstruction& Instruction : Plan.Instructions)
        {
            if (Instruction.BehaviorId == BriefGazeBreakBehaviorId && !Instruction.bPreserveOriginal && Instruction.Weight > 0.0f)
            {
                OutInstruction = Instruction;
                return true;
            }
        }
        return false;
    }

    FFrameNumber SecondsToFrame(const FFrameRate& FrameRate, float Seconds)
    {
        return FrameRate.AsFrameNumber(static_cast<double>(Seconds));
    }

    void AddLocationKey(UMovieScene3DTransformSection* TransformSection, const FName& ChannelName, FFrameNumber Frame, double Value)
    {
        if (!TransformSection) return;
        TMovieSceneChannelHandle<FMovieSceneDoubleChannel> ChannelHandle = TransformSection->GetChannelProxy().GetChannelByName<FMovieSceneDoubleChannel>(ChannelName);
        if (FMovieSceneDoubleChannel* Channel = ChannelHandle.Get())
        {
            Channel->AddLinearKey(Frame, Value);
        }
    }

    void AddLocationKeys(UMovieScene3DTransformSection* TransformSection, FFrameNumber Frame, const FVector& Location)
    {
        AddLocationKey(TransformSection, TEXT("Location.X"), Frame, Location.X);
        AddLocationKey(TransformSection, TEXT("Location.Y"), Frame, Location.Y);
        AddLocationKey(TransformSection, TEXT("Location.Z"), Frame, Location.Z);
    }

    void AddEyeControlKeys(
        UMovieSceneControlRigParameterSection* Section,
        const FName& ControlName,
        FFrameNumber StartFrame,
        FFrameNumber AwayFrame,
        FFrameNumber ReturnFrame,
        const FVector2D& AwayValue)
    {
        if (!Section) return;
        Section->AddVector2DParameter(ControlName, FVector2D::ZeroVector, true);
        for (FVector2DParameterNameAndCurves& Parameter : Section->GetVector2DParameterNamesAndCurves())
        {
            if (Parameter.ParameterName == ControlName)
            {
                Parameter.XCurve.AddLinearKey(StartFrame, 0.0f);
                Parameter.YCurve.AddLinearKey(StartFrame, 0.0f);
                Parameter.XCurve.AddLinearKey(AwayFrame, AwayValue.X);
                Parameter.YCurve.AddLinearKey(AwayFrame, AwayValue.Y);
                Parameter.XCurve.AddLinearKey(ReturnFrame, 0.0f);
                Parameter.YCurve.AddLinearKey(ReturnFrame, 0.0f);
                break;
            }
        }
    }

#include "MovieSceneSection.h"

    void AddEyelidControlKeys(
        UMovieSceneControlRigParameterSection* Section,
        const FName& ControlName,
        FFrameNumber StartFrame,
        FFrameNumber CloseFrame,
        FFrameNumber OpenFrame)
    {
        if (!Section) return;
        Section->AddScalarParameter(ControlName, 0.0f, true);
        for (FScalarParameterNameAndCurve& Parameter : Section->GetScalarParameterNamesAndCurves())
        {
            if (Parameter.ParameterName == ControlName)
            {
                // Generate 4 distinct, visible blinks across the timeline
                const int32 FrameStep = 30; // Every 1 second (30 frames)
                for (int32 i = 0; i < 4; ++i)
                {
                    const FFrameNumber BlinkStart = StartFrame + FFrameNumber(15 + i * FrameStep);
                    const FFrameNumber BlinkPeak  = BlinkStart + FFrameNumber(5);
                    const FFrameNumber BlinkEnd   = BlinkStart + FFrameNumber(10);

                    Parameter.ParameterCurve.AddLinearKey(BlinkStart, 0.0f);
                    Parameter.ParameterCurve.AddLinearKey(BlinkPeak,  1.0f);
                    Parameter.ParameterCurve.AddLinearKey(BlinkEnd,   0.0f);
                }
                break;
            }
        }
    }

    USkeletalMeshComponent* FindMetaHumanFaceComponent(AActor* Actor)
    {
        if (!Actor) return nullptr;

        TArray<USkeletalMeshComponent*> SkeletalComponents;
        Actor->GetComponents<USkeletalMeshComponent>(SkeletalComponents, true);

        TArray<UChildActorComponent*> ChildActors;
        Actor->GetComponents<UChildActorComponent>(ChildActors);
        for (UChildActorComponent* CAC : ChildActors)
        {
            if (AActor* Child = CAC->GetChildActor())
            {
                // GetComponents resets the output array — collect separately and append
                TArray<USkeletalMeshComponent*> ChildComponents;
                Child->GetComponents<USkeletalMeshComponent>(ChildComponents, true);
                SkeletalComponents.Append(ChildComponents);
            }
        }

        for (USkeletalMeshComponent* Component : SkeletalComponents)
        {
            const FString ComponentName = Component ? Component->GetName() : FString();
            const FString MeshName = Component && Component->GetSkeletalMeshAsset()
                ? Component->GetSkeletalMeshAsset()->GetName() : FString();
            if (Component && (ComponentName.Equals(TEXT("Face"), ESearchCase::IgnoreCase) || MeshName.Contains(TEXT("FaceMesh"), ESearchCase::IgnoreCase)))
            {
                return Component;
            }
        }
        return nullptr;
    }

    USkeletalMeshComponent* FindMetaHumanBodyComponent(AActor* Actor)
    {
        if (!Actor) return nullptr;

        TArray<USkeletalMeshComponent*> SkeletalComponents;
        Actor->GetComponents<USkeletalMeshComponent>(SkeletalComponents, true);

        TArray<UChildActorComponent*> ChildActors;
        Actor->GetComponents<UChildActorComponent>(ChildActors);
        for (UChildActorComponent* CAC : ChildActors)
        {
            if (AActor* Child = CAC->GetChildActor())
            {
                // GetComponents resets the output array — collect separately and append
                TArray<USkeletalMeshComponent*> ChildComponents;
                Child->GetComponents<USkeletalMeshComponent>(ChildComponents, true);
                SkeletalComponents.Append(ChildComponents);
            }
        }

        for (USkeletalMeshComponent* Component : SkeletalComponents)
        {
            const FString ComponentName = Component ? Component->GetName() : FString();
            const FString MeshName = Component && Component->GetSkeletalMeshAsset()
                ? Component->GetSkeletalMeshAsset()->GetName() : FString();
            if (Component && (ComponentName.Equals(TEXT("Body"), ESearchCase::IgnoreCase)
                || ComponentName.Equals(TEXT("Torso"), ESearchCase::IgnoreCase)
                || MeshName.Contains(TEXT("BodyMesh"), ESearchCase::IgnoreCase)))
            {
                return Component;
            }
        }
        return nullptr;
    }

    AActor* FindMetaHumanActor(UWorld* World)
    {
        if (!World) return nullptr;
        for (FActorIterator It(World); It; ++It)
        {
            AActor* Candidate = *It;
            if (Candidate && FindMetaHumanFaceComponent(Candidate))
            {
                return Candidate;
            }
        }
        return nullptr;
    }

    float ParseFloatTextBox(const TSharedPtr<SEditableTextBox>& TextBox, float DefaultValue)
    {
        if (!TextBox.IsValid()) return DefaultValue;
        const FString RawValue = TextBox->GetText().ToString().TrimStartAndEnd();
        return RawValue.IsEmpty() ? DefaultValue : FCString::Atof(*RawValue);
    }

    struct FGeneratedTakeInfo
    {
        FString TakeName;
        // Asset path of this take's dedicated Level Sequence (one sequence per take)
        FString SequencePath;
        FString StatusText;
        FString OutputText;
    };
}

// ============================================================================
//  SMHPDDirectorPanel
// ============================================================================
class SMHPDDirectorPanel : public SCompoundWidget
{
public:
    SLATE_BEGIN_ARGS(SMHPDDirectorPanel) {}
    SLATE_END_ARGS()

    using FBodyOptionPtr = TSharedPtr<FString>;

    // -------------------------------------------------------------------------
    // Member variables
    // -------------------------------------------------------------------------

    // Phase 1
    TSharedPtr<SEditableTextBox>        BaselineTakeNameTextBox;
    TSharedPtr<STextBlock>              AudioFilePathText;
    TSharedPtr<STextBlock>              BaselineStatusText;
    FString                             SelectedAudioFilePath;
    TWeakObjectPtr<ULevelSequence>      ActiveBaselineSequence;
    FString                             ActiveBaselineTakeName;

    // Phase 2
    bool                                bHasLastPlan = false;
    FMHPDPerformancePlan                LastPlan;
    FString                             LastGeneratedTakeName;
    float                               Intensity = 1.0f;

    TArray<TSharedPtr<FGeneratedTakeInfo>>  TakeHistoryList;
    TSharedPtr<FGeneratedTakeInfo>          SelectedTake;
    TSharedPtr<SComboBox<TSharedPtr<FGeneratedTakeInfo>>> TakeHistoryComboBox;

    // Body animation library
    TArray<FBodyOptionPtr>               BodyLibraryOptions;
    FBodyOptionPtr                       SelectedBodyOption;
    TSharedPtr<SComboBox<FBodyOptionPtr>> BodyLibraryComboBox;

    // Voice
    TSharedPtr<FInteractiveProcess>     VoiceProcess;
    TSharedPtr<SButton>                 RecordVoiceButton;

    // Direction inputs
    TSharedPtr<SEditableTextBox>        SourceTakeTextBox;
    TSharedPtr<SEditableTextBox>        RangeStartTextBox;
    TSharedPtr<SEditableTextBox>        RangeEndTextBox;
    TSharedPtr<SMultiLineEditableTextBox> DirectionTextBox;
    TSharedPtr<SMultiLineEditableTextBox> FollowUpTextBox;
    TSharedPtr<SMultiLineEditableTextBox> PlanTextBox;
    TSharedPtr<STextBlock>              IntensityLabel;
    TSharedPtr<STextBlock>              TakeStatusText;

    // Lock checkboxes
    TSharedPtr<SCheckBox>               DialogueAudioCheckBox;
    TSharedPtr<SCheckBox>               LipSyncCheckBox;
    TSharedPtr<SCheckBox>               FacialAnimationCheckBox;
    TSharedPtr<SCheckBox>               GazeCheckBox;
    TSharedPtr<SCheckBox>               BodyAnimationCheckBox;
    TSharedPtr<SCheckBox>               TimingCheckBox;
    void Construct(const FArguments& InArgs)
    {
        Intensity = 1.0f;

        ChildSlot
        [
            SNew(SBorder)
            .Padding(12.0f)
            .BorderImage(FAppStyle::GetBrush("Brushes.Panel"))
            [
                SNew(SScrollBox)
                + SScrollBox::Slot()
                [
                    SNew(SVerticalBox)

                    // --------------------------------------------------------
                    // Title
                    // --------------------------------------------------------
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("PanelTitle", "MetaHuman Performance Director"))
                        .Font(FAppStyle::GetFontStyle("DetailsView.CategoryFontStyle"))
                    ]

                    // ========================================================
                    // PHASE 1 — GENERATE BASELINE TAKE
                    // ========================================================
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("Phase1Label", "1  —  Generate Baseline Take"))
                        .Font(FAppStyle::GetFontStyle("DetailsView.CategoryFontStyle"))
                    ]

                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 8.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("Phase1Desc", "Import audio and generate a MetaHuman facial animation baseline. This creates a Level Sequence with audio and lip-sync tracks ready for acting direction."))
                        .AutoWrapText(true)
                    ]

                    // Take name field
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 8.0f)
                    [
                        MakeTextInputRow(BaselineTakeNameTextBox, LOCTEXT("TakeNameLabel", "Take name"), LOCTEXT("TakeNameDefault", "Take_001"))
                    ]

                    // Audio file row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 8.0f)
                    [
                        SNew(SVerticalBox)
                        + SVerticalBox::Slot()
                        .AutoHeight()
                        .Padding(0.0f, 0.0f, 0.0f, 4.0f)
                        [
                            SNew(STextBlock)
                            .Text(LOCTEXT("AudioFileLabel", "Audio file (.wav)"))
                        ]
                        + SVerticalBox::Slot()
                        .AutoHeight()
                        [
                            SNew(SHorizontalBox)
                            + SHorizontalBox::Slot()
                            .FillWidth(1.0f)
                            .VAlign(VAlign_Center)
                            .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                            [
                                SAssignNew(AudioFilePathText, STextBlock)
                                .Text(LOCTEXT("AudioFilePlaceholder", "No file selected"))
                                .ColorAndOpacity(FSlateColor(FLinearColor(0.6f, 0.6f, 0.6f)))
                                .AutoWrapText(true)
                            ]
                            + SHorizontalBox::Slot()
                            .AutoWidth()
                            [
                                SNew(SButton)
                                .Text(LOCTEXT("BrowseButton", "Browse..."))
                                .OnClicked(this, &SMHPDDirectorPanel::OnBrowseAudioClicked)
                            ]
                        ]
                    ]

                    // Generate Baseline button
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(SButton)
                        .Text(LOCTEXT("GenerateBaseline", "▶  Generate Baseline Take"))
                        .HAlign(HAlign_Center)
                        .ButtonColorAndOpacity(FLinearColor(0.18f, 0.55f, 0.28f, 1.0f))
                        .OnClicked(this, &SMHPDDirectorPanel::OnGenerateBaselineTakeClicked)
                    ]

                    // Baseline status text
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 4.0f)
                    [
                        SAssignNew(BaselineStatusText, STextBlock)
                        .Text(LOCTEXT("BaselineStatusReady", "Select a .wav file and click Generate."))
                        .ColorAndOpacity(FSlateColor(FLinearColor(0.6f, 0.6f, 0.6f)))
                        .AutoWrapText(true)
                    ]

                    // Open in Sequencer + Reset Actor utility row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 4.0f, 0.0f, 12.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        .Padding(0.0f, 0.0f, 6.0f, 0.0f)
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("OpenInSequencer", "Open Take in Sequencer"))
                            .HAlign(HAlign_Center)
                            .OnClicked(this, &SMHPDDirectorPanel::OnOpenInSequencerClicked)
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("ResetActorBtn", "↻ Reset Actor Instance"))
                            .ToolTipText(LOCTEXT("ResetActorTooltip", "Respawns a clean instance of the level MetaHuman at the exact same location with stock Blueprint defaults, clearing any bad socket attachments or instance overrides."))
                            .OnClicked(this, &SMHPDDirectorPanel::OnResetMetaHumanActorClicked)
                        ]
                    ]

                    // ========================================================
                    // Divider
                    // ========================================================
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 4.0f, 0.0f, 12.0f)
                    [
                        SNew(SSeparator)
                    ]

                    // ========================================================
                    // PHASE 2 — DIRECT THE PERFORMANCE
                    // ========================================================
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("Phase2Label", "2  —  Direct the Performance"))
                        .Font(FAppStyle::GetFontStyle("DetailsView.CategoryFontStyle"))
                    ]

                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("Phase2Desc", "Type an acting direction. Each take generates an isolated Level Sequence so you can A/B compare instantly from the take dropdown."))
                        .AutoWrapText(true)
                    ]

                    // Timeline range row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("TimelineRangeLabel", "Timeline range"))
                    ]

                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 10.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            MakeTextInputRow(SourceTakeTextBox, LOCTEXT("SourceTakeLabel", "Source take"), LOCTEXT("SourceTakeDefault", "Current Sequencer Take"))
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            MakeTextInputRow(RangeStartTextBox, LOCTEXT("RangeStartLabel", "Start seconds"), LOCTEXT("RangeStartDefault", "0.0"), 120.0f)
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            MakeTextInputRow(RangeEndTextBox, LOCTEXT("RangeEndLabel", "End seconds"), LOCTEXT("RangeEndDefault", "10.0"), 120.0f)
                        ]
                    ]

                    // Director note label + voice button row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .VAlign(VAlign_Center)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SNew(STextBlock)
                            .Text(LOCTEXT("DirectionLabel", "Director note"))
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            SAssignNew(RecordVoiceButton, SButton)
                            .Text(this, &SMHPDDirectorPanel::GetRecordVoiceButtonText)
                            .OnPressed(this, &SMHPDDirectorPanel::OnRecordVoicePressed)
                            .OnReleased(this, &SMHPDDirectorPanel::OnRecordVoiceReleased)
                            .ButtonColorAndOpacity(FLinearColor(0.8f, 0.2f, 0.2f))
                        ]
                    ]

                    // Direction text box
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SBox)
                        .MinDesiredHeight(96.0f)
                        [
                            SAssignNew(DirectionTextBox, SMultiLineEditableTextBox)
                            .Text(LOCTEXT("DirectionPlaceholder", "She is nervous, but trying to appear confident. Have her briefly look away before answering."))
                            .AutoWrapText(true)
                        ]
                    ]

                    // Follow-up label
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("FollowUpLabel", "Optional follow-up note"))
                    ]

                    // Follow-up text box
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SBox)
                        .MinDesiredHeight(54.0f)
                        [
                            SAssignNew(FollowUpTextBox, SMultiLineEditableTextBox)
                            .HintText(LOCTEXT("FollowUpHint", "Example: That is close. Keep the gaze change, but make the facial tension less obvious."))
                            .AutoWrapText(true)
                        ]
                    ]

                    // Intensity label
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SAssignNew(IntensityLabel, STextBlock)
                        .Text(GetIntensityText())
                    ]

                    // Intensity slider
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SSlider)
                        .Value(Intensity)
                        .ToolTipText(LOCTEXT("PerformanceSizeTooltip", "How big the adjustment plays — from barely perceptible to full. Scales how far the face moves, not how fast."))
                        .OnValueChanged(this, &SMHPDDirectorPanel::OnIntensityChanged)
                    ]

                    // Body micro-behavior dropdown label & scan button
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .VAlign(VAlign_Center)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SNew(STextBlock)
                            .Text(LOCTEXT("BodyLibraryLabel", "Body micro-behavior (optional)"))
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("ScanBodyLibBtn", "↻ Scan Library"))
                            .OnClicked(this, &SMHPDDirectorPanel::OnScanBodyLibraryClicked)
                        ]
                    ]

                    // Body micro-behavior dropdown
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        [
                            SAssignNew(BodyLibraryComboBox, SComboBox<FBodyOptionPtr>)
                            .OptionsSource(&BodyLibraryOptions)
                            .OnGenerateWidget(this, &SMHPDDirectorPanel::GenerateBodyLibraryRow)
                            .OnSelectionChanged(this, &SMHPDDirectorPanel::OnBodyLibrarySelectionChanged)
                            .ContentPadding(4.0f)
                            [
                                SNew(STextBlock)
                                .Text(this, &SMHPDDirectorPanel::GetSelectedBodyLibraryText)
                            ]
                        ]
                    ]

                    // Preserve channels label
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("LocksLabel", "Preserve channels"))
                    ]

                    // Lock checkboxes
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        [
                            MakeLockColumn(true)
                        ]
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        [
                            MakeLockColumn(false)
                        ]
                    ]

                    // Action buttons row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("AddActingTake", "✦  Add Acting Take"))
                            .HAlign(HAlign_Center)
                            .ButtonColorAndOpacity(FLinearColor(0.12f, 0.45f, 0.90f, 1.0f))
                            .OnClicked(this, &SMHPDDirectorPanel::OnGenerateAndCreateClicked)
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("GeneratePlan", "Generate Plan Only"))
                            .OnClicked(this, &SMHPDDirectorPanel::OnGeneratePlanClicked)
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("ClearFollowUp", "Clear Follow-Up"))
                            .OnClicked(this, &SMHPDDirectorPanel::OnClearFollowUpClicked)
                        ]
                    ]

                    // Take history row
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SNew(SHorizontalBox)
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        .VAlign(VAlign_Center)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SNew(STextBlock)
                            .Text(LOCTEXT("TakeHistoryLabel", "Acting takes:"))
                        ]
                        + SHorizontalBox::Slot()
                        .FillWidth(1.0f)
                        .Padding(0.0f, 0.0f, 8.0f, 0.0f)
                        [
                            SAssignNew(TakeHistoryComboBox, SComboBox<TSharedPtr<FGeneratedTakeInfo>>)
                            .OptionsSource(&TakeHistoryList)
                            .OnGenerateWidget(this, &SMHPDDirectorPanel::GenerateTakeHistoryRow)
                            .OnSelectionChanged(this, &SMHPDDirectorPanel::OnTakeSelectionChanged)
                            .ContentPadding(4.0f)
                            [
                                SNew(STextBlock)
                                .Text(this, &SMHPDDirectorPanel::GetSelectedTakeText)
                            ]
                        ]
                        + SHorizontalBox::Slot()
                        .AutoWidth()
                        [
                            SNew(SButton)
                            .Text(LOCTEXT("RemoveTakeBtn", "Delete Take"))
                            .ToolTipText(LOCTEXT("RemoveTakeTooltip", "Remove the currently selected take from the dropdown list."))
                            .OnClicked(this, &SMHPDDirectorPanel::OnRemoveTakeClicked)
                            .IsEnabled(this, &SMHPDDirectorPanel::CanRemoveSelectedTake)
                        ]
                    ]

                    // Divider
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 8.0f)
                    [
                        SNew(SSeparator)
                    ]

                    // Take status label
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("TakeStatusLabel", "Take status"))
                    ]

                    // Take status text
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 12.0f)
                    [
                        SAssignNew(TakeStatusText, STextBlock)
                        .Text(LOCTEXT("TakeStatusPlaceholder", "Generate a baseline, then add acting takes to layer performances non-destructively."))
                        .AutoWrapText(true)
                    ]

                    // Plan label
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    .Padding(0.0f, 0.0f, 0.0f, 6.0f)
                    [
                        SNew(STextBlock)
                        .Text(LOCTEXT("PlanLabel", "Structured performance plan"))
                    ]

                    // Plan text box
                    + SVerticalBox::Slot()
                    .AutoHeight()
                    [
                        SNew(SBox)
                        .MinDesiredHeight(260.0f)
                        [
                            SAssignNew(PlanTextBox, SMultiLineEditableTextBox)
                            .Text(LOCTEXT("PlanPlaceholder", "Generate a plan to preview interpreted intent, locked channels, timeline region, and editable output instructions."))
                            .AutoWrapText(true)
                            .IsReadOnly(true)
                        ]
                    ]
                ]
            ]
        ];

        ScanBodyLibrary();
    }

private:

    // -------------------------------------------------------------------------
    // Helper UI builders & handlers
    // -------------------------------------------------------------------------

    // -------------------------------------------------------------------------
    // Phase 1 — Generate Baseline Take
    // -------------------------------------------------------------------------

    FReply OnBrowseAudioClicked()
    {
        IDesktopPlatform* DesktopPlatform = FDesktopPlatformModule::Get();
        if (!DesktopPlatform)
        {
            return FReply::Handled();
        }

        TArray<FString> OutFiles;
        const bool bOpened = DesktopPlatform->OpenFileDialog(
            FSlateApplication::Get().FindBestParentWindowHandleForDialogs(AsShared()),
            TEXT("Select dialogue audio (.wav)"),
            FPaths::GetPath(SelectedAudioFilePath),
            TEXT(""),
            TEXT("Audio Files (*.wav)|*.wav"),
            EFileDialogFlags::None,
            OutFiles
        );

        if (bOpened && OutFiles.Num() > 0)
        {
            SelectedAudioFilePath = OutFiles[0];
            if (AudioFilePathText.IsValid())
            {
                AudioFilePathText->SetText(FText::FromString(SelectedAudioFilePath));
                AudioFilePathText->SetColorAndOpacity(FSlateColor(FLinearColor::White));
            }
        }

        return FReply::Handled();
    }

    FReply OnResetMetaHumanActorClicked()
    {
        if (!GEditor) return FReply::Handled();

        UWorld* World = GEditor->GetEditorWorldContext().World();
        if (!World) return FReply::Handled();

        AActor* MetaHumanActor = FindMetaHumanActor(World);
        if (!MetaHumanActor)
        {
            SetBaselineStatus(TEXT("No MetaHuman actor found in the active level to reset."), true);
            return FReply::Handled();
        }

        const FTransform ActorTransform = MetaHumanActor->GetTransform();
        const FString ActorLabel = MetaHumanActor->GetActorLabel();
        UClass* ActorClass = MetaHumanActor->GetClass();

        // Reset component animation modes back to AnimationBlueprint
        if (USkeletalMeshComponent* FaceComp = FindMetaHumanFaceComponent(MetaHumanActor))
        {
            FaceComp->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        }
        if (USkeletalMeshComponent* BodyComp = FindMetaHumanBodyComponent(MetaHumanActor))
        {
            BodyComp->SetAnimationMode(EAnimationMode::AnimationBlueprint);
        }

        // Destroy mutated level instance
        World->DestroyActor(MetaHumanActor);

        // Respawn a clean instance with stock Blueprint defaults at exact same transform
        FActorSpawnParameters SpawnParams;
        SpawnParams.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
        AActor* NewActor = World->SpawnActor(ActorClass, &ActorTransform, SpawnParams);
        if (NewActor)
        {
            NewActor->SetActorLabel(ActorLabel);
            GEditor->RedrawAllViewports();
            SetBaselineStatus(FString::Printf(TEXT("Successfully reset '%s' to clean Blueprint defaults."), *ActorLabel), false);
        }
        else
        {
            SetBaselineStatus(TEXT("Failed to respawn MetaHuman actor. Check Output Log."), true);
        }

        return FReply::Handled();
    }

    FReply OnGenerateBaselineTakeClicked()
    {
        // Validate inputs
        const FString TakeName = BaselineTakeNameTextBox.IsValid()
            ? BaselineTakeNameTextBox->GetText().ToString().TrimStartAndEnd()
            : FString();

        if (TakeName.IsEmpty())
        {
            SetBaselineStatus(TEXT("Please enter a take name."), true);
            return FReply::Handled();
        }

        if (SelectedAudioFilePath.IsEmpty())
        {
            SetBaselineStatus(TEXT("Please select a .wav audio file first."), true);
            return FReply::Handled();
        }

        SetBaselineStatus(TEXT("Processing... Please wait. This may take 30-60 seconds."), false);

        // Invoke the Python baseline generation script
        IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
        if (!PythonPlugin)
        {
            SetBaselineStatus(TEXT("Error: Python plugin is not available. Enable the Python Script Plugin in your project settings."), true);
            return FReply::Handled();
        }

        const FString SafeAudioPath = SelectedAudioFilePath.Replace(TEXT("\\"), TEXT("/"));
        const FString OutputDir     = FString::Printf(TEXT("/Game/MHPD/%s"), *MakeAssetSafeName(TakeName));

        const FString PythonCmd = FString::Printf(
            TEXT("import importlib, generate_baseline; importlib.reload(generate_baseline); generate_baseline.main(audio_path=r'%s', output_dir='%s')"),
            *SelectedAudioFilePath,
            *OutputDir
        );

        PythonPlugin->ExecPythonCommand(*PythonCmd);

        // Now build the Level Sequence from the generated assets
        const bool bSuccess = CreateBaselineLevelSequence(TakeName, OutputDir);
        if (bSuccess)
        {
            SetBaselineStatus(FString::Printf(TEXT("✓ Baseline generated: %s\nSequencer opened automatically."), *OutputDir), false);
        }
        else
        {
            SetBaselineStatus(TEXT("Baseline assets generated (check Output Log). Open the Sequencer manually from the Content Browser if it did not open automatically."), false);
        }

        return FReply::Handled();
    }

    // HEAD-FOLLOWS-BODY BAKE (see TECHNICAL_REPORT_HEAD_STRETCHING.md).
    // In AnimationCustomMode the Face component evaluates ONLY the take asset, so
    // the face skeleton's own copy of the core body chain (root..spine..neck..head)
    // would sit at ref pose while the Body component animates — tearing the head
    // off the neck. Copying the body animation's bone tracks into the take makes a
    // single AnimSequence carry both the facial curves and the matching body-chain
    // motion. Bones absent from the face skeleton (arms, legs) are skipped.
    //
    // This lives in C++ because UAnimSequenceBase::GetController() is not a
    // UFUNCTION — Python cannot obtain the animation data controller at all.
    int32 BakeBodyChainIntoFaceAnim(UAnimSequence* FaceAnim, UAnimSequence* BodyAnim)
    {
        if (!FaceAnim || !BodyAnim) return 0;

        IAnimationDataModel* FaceModel = FaceAnim->GetDataModel();
        IAnimationDataModel* BodyModel = BodyAnim->GetDataModel();
        const USkeleton* FaceSkeleton = FaceAnim->GetSkeleton();
        if (!FaceModel || !BodyModel || !FaceSkeleton)
        {
            UE_LOG(LogTemp, Warning, TEXT("MHPD: Body-chain bake skipped - missing data model or skeleton"));
            return 0;
        }

        const int32 NumKeys = FaceModel->GetNumberOfKeys();
        if (NumKeys <= 0)
        {
            UE_LOG(LogTemp, Warning, TEXT("MHPD: Body-chain bake skipped - take has no keys"));
            return 0;
        }

        const FFrameRate FaceRate = FaceModel->GetFrameRate();
        const FFrameRate BodyRate = BodyModel->GetFrameRate();
        const double BodyLength = static_cast<double>(BodyAnim->GetPlayLength());

        TArray<FName> BodyBoneNames;
        BodyModel->GetBoneTrackNames(BodyBoneNames);

        FaceAnim->Modify();
        IAnimationDataController& Controller = FaceAnim->GetController();
        Controller.OpenBracket(LOCTEXT("MHPDBakeBodyChain", "MHPD Bake Body Chain"), false);

        static const TMap<FName, FName> BodyToFaceBoneMap = {
            { FName(TEXT("neck_01")), FName(TEXT("FACIAL_C_Neck1Root")) },
            { FName(TEXT("neck_02")), FName(TEXT("FACIAL_C_Neck2Root")) },
            { FName(TEXT("head")),    FName(TEXT("FACIAL_C_FacialRoot")) }
        };

        int32 CopiedBones = 0;
        int32 SkippedBones = 0;
        for (const FName& BodyBoneName : BodyBoneNames)
        {
            FName TargetBoneName = BodyBoneName;
            if (FaceSkeleton->GetReferenceSkeleton().FindBoneIndex(TargetBoneName) == INDEX_NONE)
            {
                if (const FName* Mapped = BodyToFaceBoneMap.Find(BodyBoneName))
                {
                    TargetBoneName = *Mapped;
                }
            }

            if (FaceSkeleton->GetReferenceSkeleton().FindBoneIndex(TargetBoneName) == INDEX_NONE && BodyBoneName == FName(TEXT("head")))
            {
                TargetBoneName = FName(TEXT("FACIAL_C_Head"));
            }

            const int32 TargetBoneIdx = FaceSkeleton->GetReferenceSkeleton().FindBoneIndex(TargetBoneName);
            if (TargetBoneIdx == INDEX_NONE)
            {
                ++SkippedBones;
                continue;
            }

            const FVector3f CanonicalRefTranslation = FVector3f(FaceSkeleton->GetReferenceSkeleton().GetRefBonePose()[TargetBoneIdx].GetTranslation());
            const FVector3f CanonicalRefScale = FVector3f(FaceSkeleton->GetReferenceSkeleton().GetRefBonePose()[TargetBoneIdx].GetScale3D());

            if (FaceModel->IsValidBoneTrackName(TargetBoneName))
            {
                Controller.RemoveBoneTrack(TargetBoneName, false);
            }
            if (!Controller.AddBoneCurve(TargetBoneName, false))
            {
                ++SkippedBones;
                continue;
            }

            TArray<FVector3f> PositionKeys;
            TArray<FQuat4f>   RotationKeys;
            TArray<FVector3f> ScaleKeys;
            PositionKeys.Reserve(NumKeys);
            RotationKeys.Reserve(NumKeys);
            ScaleKeys.Reserve(NumKeys);

            for (int32 KeyIndex = 0; KeyIndex < NumKeys; ++KeyIndex)
            {
                // Hold the body's final pose if the gesture is shorter than the take
                const double TimeSeconds = FMath::Min(FaceRate.AsSeconds(FFrameNumber(KeyIndex)), BodyLength);
                const FTransform BoneTransform = BodyModel->EvaluateBoneTrackTransform(
                    BodyBoneName, BodyRate.AsFrameTime(TimeSeconds), EAnimInterpolationType::Linear);

                // Preserve the Face skeleton's canonical reference translation and scale; copy only rotation
                PositionKeys.Add(CanonicalRefTranslation);
                RotationKeys.Add(FQuat4f(BoneTransform.GetRotation()));
                ScaleKeys.Add(CanonicalRefScale);
            }

            Controller.SetBoneTrackKeys(TargetBoneName, PositionKeys, RotationKeys, ScaleKeys, false);
            ++CopiedBones;
        }

        Controller.CloseBracket(false);

        FaceAnim->PostEditChange();
        FaceAnim->MarkPackageDirty();

        UE_LOG(LogTemp, Log, TEXT("MHPD: Body-chain bake copied %d bone track(s) over %d keys (%d body bones not in face skeleton)"),
            CopiedBones, NumKeys, SkippedBones);

        if (CopiedBones == 0)
        {
            UE_LOG(LogTemp, Warning, TEXT("MHPD: No body bones matched the face skeleton - the head will NOT follow the body. ")
                TEXT("Check that the body animation targets the MetaHuman base skeleton."));
            return 0;
        }

        // Persist the modified take (Python already saved it before this pass)
        TArray<UPackage*> PackagesToSave;
        PackagesToSave.Add(FaceAnim->GetOutermost());
        FEditorFileUtils::PromptForCheckoutAndSave(PackagesToSave, /*bCheckDirty*/ false, /*bPromptToSave*/ false);

        return CopiedBones;
    }

    // Reference-pose component-space rotation of a bone (accumulate local ref
    // transforms from the bone up to the root).
    static FQuat GetRefPoseComponentRotation(const FReferenceSkeleton& RefSkel, int32 BoneIndex)
    {
        FQuat Accum = FQuat::Identity;
        for (int32 Idx = BoneIndex; Idx != INDEX_NONE; Idx = RefSkel.GetParentIndex(Idx))
        {
            Accum = RefSkel.GetRefBonePose()[Idx].GetRotation() * Accum;
        }
        return Accum;
    }

    // HEAD & NECK MOTION (see TECHNICAL_REPORT_HEAD_AND_NECK_MOVEMENT.md).
    //
    // Gross head rotation belongs to the BODY skeleton (metahuman_base_skel:
    // neck_01 -> neck_02 -> head), NOT the face skeleton. Keying it on face bones
    // produces nothing visible: RigLogic re-drives the facial joints each frame,
    // and the face mesh is pinned to the body's attachment regardless.
    //
    // So we synthesize a body-skeleton AnimSequence carrying the rotation, play it
    // on the Body binding, and let BakeBodyChainIntoFaceAnim copy that same chain
    // into the face take so the face rides the skull. If the director also picked
    // a Body Library gesture, that clip seeds this asset and the head rotation is
    // layered on top, so both survive.
    UAnimSequence* GenerateHeadMotionBodyAnim(
        const FMHPDPerformancePlan& Plan,
        USkeleton* BodySkeleton,
        UAnimSequence* SeedBodyAnim,
        const FString& OutputDir,
        const FString& AssetName,
        int32 NumKeys,
        FFrameRate FrameRate,
        double SeqLength)
    {
        if (!BodySkeleton || NumKeys <= 0) return nullptr;

        TArray<FMHPDChannelInstruction> HeadInstructions;
        for (const FMHPDChannelInstruction& Inst : Plan.Instructions)
        {
            if (Inst.Channel == EMHPDPerformanceChannel::HeadMovement
                && Inst.Weight > 0.0f && !Inst.bPreserveOriginal)
            {
                HeadInstructions.Add(Inst);
            }
        }
        if (HeadInstructions.Num() == 0) return nullptr;

        const FReferenceSkeleton& RefSkel = BodySkeleton->GetReferenceSkeleton();
        if (RefSkel.FindBoneIndex(FName(TEXT("head"))) == INDEX_NONE)
        {
            UE_LOG(LogTemp, Warning, TEXT("MHPD: Body skeleton has no 'head' bone - cannot generate head motion"));
            return nullptr;
        }

        // Anatomical distribution down the cervical chain so the neck bends
        // instead of the skull snapping on a rigid joint.
        const TArray<TPair<FName, float>> CervicalChain = {
            TPair<FName, float>(FName(TEXT("neck_01")), 0.20f),
            TPair<FName, float>(FName(TEXT("neck_02")), 0.30f),
            TPair<FName, float>(FName(TEXT("head")),    0.50f)
        };

        const FString PkgPath = FString::Printf(TEXT("%s/%s"), *OutputDir, *AssetName);
        UPackage* Package = CreatePackage(*PkgPath);
        if (!Package) return nullptr;

        UAnimSequence* BodyAnim = NewObject<UAnimSequence>(Package, *AssetName, RF_Public | RF_Standalone | RF_Transactional);
        if (!BodyAnim) return nullptr;
        BodyAnim->SetSkeleton(BodySkeleton);

        IAnimationDataController& Controller = BodyAnim->GetController();
        Controller.OpenBracket(LOCTEXT("MHPDGenHeadMotion", "MHPD Generate Head Motion"), false);
        Controller.InitializeModel();
        Controller.SetFrameRate(FrameRate, false);
        Controller.SetNumberOfFrames(FFrameNumber(FMath::Max(1, NumKeys - 1)), false);

        IAnimationDataModel* SeedModel = SeedBodyAnim ? SeedBodyAnim->GetDataModel() : nullptr;
        const double SeedLength = SeedBodyAnim ? static_cast<double>(SeedBodyAnim->GetPlayLength()) : 0.0;
        const FFrameRate SeedRate = SeedModel ? SeedModel->GetFrameRate() : FrameRate;

        // Write every bone the seed gesture animates, plus the cervical chain
        TArray<FName> BonesToWrite;
        if (SeedModel)
        {
            SeedModel->GetBoneTrackNames(BonesToWrite);
        }
        for (const TPair<FName, float>& Pair : CervicalChain)
        {
            if (RefSkel.FindBoneIndex(Pair.Key) != INDEX_NONE)
            {
                BonesToWrite.AddUnique(Pair.Key);
            }
        }

        const double RangeStart = FMath::Clamp(static_cast<double>(Plan.RevisionRange.StartSeconds), 0.0, SeqLength);
        const double RangeEnd = (Plan.RevisionRange.EndSeconds > Plan.RevisionRange.StartSeconds)
            ? FMath::Clamp(static_cast<double>(Plan.RevisionRange.EndSeconds), RangeStart, SeqLength)
            : SeqLength;
        const double RangeDur = RangeEnd - RangeStart;

        int32 WrittenBones = 0;
        for (const FName& BoneName : BonesToWrite)
        {
            const int32 BoneIdx = RefSkel.FindBoneIndex(BoneName);
            if (BoneIdx == INDEX_NONE) continue;

            float ChainWeight = 0.0f;
            for (const TPair<FName, float>& Pair : CervicalChain)
            {
                if (Pair.Key == BoneName) { ChainWeight = Pair.Value; break; }
            }

            // Rotation is authored in COMPONENT space (Z up, +X forward) and then
            // conjugated into this bone's local space, so yaw/pitch/roll mean the
            // same thing regardless of how the bone's own axes are oriented.
            const int32 ParentIdx = RefSkel.GetParentIndex(BoneIdx);
            const FQuat ParentCS = (ParentIdx != INDEX_NONE)
                ? GetRefPoseComponentRotation(RefSkel, ParentIdx) : FQuat::Identity;
            const FQuat ParentCSInv = ParentCS.Inverse();
            const FTransform RefLocal = RefSkel.GetRefBonePose()[BoneIdx];

            TArray<FVector3f> PositionKeys;
            TArray<FQuat4f>   RotationKeys;
            TArray<FVector3f> ScaleKeys;
            PositionKeys.Reserve(NumKeys);
            RotationKeys.Reserve(NumKeys);
            ScaleKeys.Reserve(NumKeys);

            for (int32 KeyIndex = 0; KeyIndex < NumKeys; ++KeyIndex)
            {
                const double TimeSeconds = FrameRate.AsSeconds(FFrameNumber(KeyIndex));

                FTransform Base = RefLocal;
                if (SeedModel && SeedModel->IsValidBoneTrackName(BoneName))
                {
                    const double SeedTime = (SeedLength > 0.0) ? FMath::Min(TimeSeconds, SeedLength) : 0.0;
                    Base = SeedModel->EvaluateBoneTrackTransform(
                        BoneName, SeedRate.AsFrameTime(SeedTime), EAnimInterpolationType::Linear);
                }

                double Yaw = 0.0, Pitch = 0.0, Roll = 0.0;
                if (ChainWeight > 0.0f && RangeDur > 0.0
                    && TimeSeconds >= RangeStart && TimeSeconds <= RangeEnd)
                {
                    // Smoothstep ease in/out so the move starts and ends at rest
                    const double RelTime = TimeSeconds - RangeStart;
                    const double Lead = FMath::Min(0.25, RangeDur * 0.15);
                    double Env = 1.0;
                    if (Lead > 0.0 && RelTime < Lead)                   Env = RelTime / Lead;
                    else if (Lead > 0.0 && RelTime > (RangeDur - Lead)) Env = (RangeDur - RelTime) / Lead;
                    Env = FMath::Clamp(Env, 0.0, 1.0);
                    Env = Env * Env * (3.0 - 2.0 * Env);

                    for (const FMHPDChannelInstruction& Inst : HeadInstructions)
                    {
                        const double W = static_cast<double>(Inst.Weight) * ChainWeight * Env;

                        // UE convention: +Yaw turns to the character's RIGHT,
                        // +Pitch raises the chin. Flip these if a take reads mirrored.
                        if (Inst.BehaviorId == FName(TEXT("head_turn_left")))        Yaw   -= 32.0 * W;
                        else if (Inst.BehaviorId == FName(TEXT("head_turn_right")))  Yaw   += 32.0 * W;
                        else if (Inst.BehaviorId == FName(TEXT("head_pitch_up")))    Pitch += 20.0 * W;
                        else if (Inst.BehaviorId == FName(TEXT("head_pitch_down")))  Pitch -= 20.0 * W;
                        else if (Inst.BehaviorId == FName(TEXT("head_tilt")))        Roll  += 18.0 * W;
                        else if (Inst.BehaviorId == FName(TEXT("head_nod")))
                        {
                            const double Phase = (RelTime / RangeDur) * 4.0 * PI;
                            Pitch -= 22.0 * ChainWeight * Env * FMath::Max(0.0, FMath::Sin(Phase));
                        }
                        else if (Inst.BehaviorId == FName(TEXT("head_shake")))
                        {
                            const double Phase = RelTime * 3.0 * 2.0 * PI;
                            Yaw += 18.0 * ChainWeight * Env * FMath::Sin(Phase);
                        }
                        else if (Inst.BehaviorId == FName(TEXT("small_recoil_then_reset")))
                        {
                            const double Phase = (RelTime / RangeDur) * 2.0 * PI;
                            Pitch += 10.0 * ChainWeight * Env * FMath::Sin(Phase);
                        }
                    }
                }

                const FQuat DeltaCS = FRotator(Pitch, Yaw, Roll).Quaternion();
                const FQuat LocalDelta = ParentCSInv * DeltaCS * ParentCS;
                FQuat NewRot = LocalDelta * Base.GetRotation();
                NewRot.Normalize();

                PositionKeys.Add(FVector3f(Base.GetTranslation()));
                RotationKeys.Add(FQuat4f(NewRot));
                ScaleKeys.Add(FVector3f(Base.GetScale3D()));
            }

            if (BodyAnim->GetDataModel() && BodyAnim->GetDataModel()->IsValidBoneTrackName(BoneName))
            {
                Controller.RemoveBoneTrack(BoneName, false);
            }
            if (Controller.AddBoneCurve(BoneName, false))
            {
                Controller.SetBoneTrackKeys(BoneName, PositionKeys, RotationKeys, ScaleKeys, false);
                ++WrittenBones;
            }
        }

        Controller.CloseBracket(false);
        BodyAnim->PostEditChange();
        FAssetRegistryModule::AssetCreated(BodyAnim);
        Package->MarkPackageDirty();

        TArray<UPackage*> PackagesToSave;
        PackagesToSave.Add(Package);
        FEditorFileUtils::PromptForCheckoutAndSave(PackagesToSave, /*bCheckDirty*/ false, /*bPromptToSave*/ false);

        UE_LOG(LogTemp, Log, TEXT("MHPD: Generated head-motion body anim '%s' - %d bone track(s), %d keys, %d head instruction(s)"),
            *AssetName, WrittenBones, NumKeys, HeadInstructions.Num());

        return BodyAnim;
    }

    // DEPRECATED - superseded by GenerateHeadMotionBodyAnim. Keying head rotation
    // onto face-skeleton bones produces no visible movement (see the technical
    // report, approaches 3-6). Retained only for reference; no longer called.
    void BakeHeadMotionIntoFaceAnim(UAnimSequence* FaceAnim, const FMHPDPerformancePlan& Plan)
    {
        if (!FaceAnim) return;

        IAnimationDataModel* FaceModel = FaceAnim->GetDataModel();
        const USkeleton* FaceSkeleton = FaceAnim->GetSkeleton();
        if (!FaceModel || !FaceSkeleton) return;

        const int32 NumKeys = FaceModel->GetNumberOfKeys();
        if (NumKeys <= 0) return;

        const FFrameRate FaceRate = FaceModel->GetFrameRate();
        const double SeqLength = static_cast<double>(FaceAnim->GetPlayLength());

        // Check if plan has HeadMovement instructions
        TArray<FMHPDChannelInstruction> HeadInstructions;
        for (const FMHPDChannelInstruction& Inst : Plan.Instructions)
        {
            if (Inst.Channel == EMHPDPerformanceChannel::HeadMovement && Inst.Weight > 0.0f && !Inst.bPreserveOriginal)
            {
                HeadInstructions.Add(Inst);
            }
        }

        if (HeadInstructions.Num() == 0) return;

        // Resolve target bones on the face skeleton with proper anatomical weight distribution.
        // If 'head' or 'FACIAL_C_Head' exists, it drives the skull and child facial joints.
        // Neck bones share flexion/rotation to avoid unnatural joint kinks.
        struct FBoneWeightTarget
        {
            FName BoneName;
            float WeightMultiplier;
        };

        TArray<FBoneWeightTarget> TargetBones;
        const FReferenceSkeleton& RefSkeleton = FaceSkeleton->GetReferenceSkeleton();

        const bool bHasNeckHeadChain = (RefSkeleton.FindBoneIndex(FName(TEXT("FACIAL_C_Neck1Root"))) != INDEX_NONE
            || RefSkeleton.FindBoneIndex(FName(TEXT("neck_01"))) != INDEX_NONE);

        if (bHasNeckHeadChain)
        {
            for (const auto& Pair : {
                TPair<FName, float>(FName(TEXT("neck_01")), 0.20f),
                TPair<FName, float>(FName(TEXT("FACIAL_C_Neck1Root")), 0.20f),
                TPair<FName, float>(FName(TEXT("neck_02")), 0.30f),
                TPair<FName, float>(FName(TEXT("FACIAL_C_Neck2Root")), 0.30f),
                TPair<FName, float>(FName(TEXT("head")), 0.50f),
                TPair<FName, float>(FName(TEXT("FACIAL_C_Head")), 0.50f)
            })
            {
                if (RefSkeleton.FindBoneIndex(Pair.Key) != INDEX_NONE)
                {
                    TargetBones.Add({ Pair.Key, Pair.Value });
                }
            }
        }
        else if (RefSkeleton.FindBoneIndex(FName(TEXT("FACIAL_C_FacialRoot"))) != INDEX_NONE)
        {
            TargetBones.Add({ FName(TEXT("FACIAL_C_FacialRoot")), 1.0f });
        }

        if (TargetBones.Num() == 0) return;

        FaceAnim->Modify();
        IAnimationDataController& Controller = FaceAnim->GetController();
        Controller.OpenBracket(LOCTEXT("MHPDBakeHeadMotion", "MHPD Bake Head Motion"), false);

        const double RangeStart = FMath::Clamp(static_cast<double>(Plan.RevisionRange.StartSeconds), 0.0, SeqLength);
        const double RangeEnd = (Plan.RevisionRange.EndSeconds > Plan.RevisionRange.StartSeconds)
            ? FMath::Clamp(static_cast<double>(Plan.RevisionRange.EndSeconds), RangeStart, SeqLength)
            : SeqLength;
        const double RangeDur = RangeEnd - RangeStart;

        for (const FBoneWeightTarget& Target : TargetBones)
        {
            const FName BoneName = Target.BoneName;
            const float BoneDistWeight = Target.WeightMultiplier;

            TArray<FVector3f> PositionKeys;
            TArray<FQuat4f>   RotationKeys;
            TArray<FVector3f> ScaleKeys;
            PositionKeys.Reserve(NumKeys);
            RotationKeys.Reserve(NumKeys);
            ScaleKeys.Reserve(NumKeys);

            const int32 BoneIdx = RefSkeleton.FindBoneIndex(BoneName);
            const FTransform RefPoseTransform = (BoneIdx != INDEX_NONE)
                ? FTransform(RefSkeleton.GetRefBonePose()[BoneIdx])
                : FTransform::Identity;

            for (int32 KeyIndex = 0; KeyIndex < NumKeys; ++KeyIndex)
            {
                const double TimeSeconds = FaceRate.AsSeconds(FFrameNumber(KeyIndex));
                FTransform CurrentTransform = RefPoseTransform;
                if (FaceModel->IsValidBoneTrackName(BoneName))
                {
                    CurrentTransform = FaceModel->EvaluateBoneTrackTransform(
                        BoneName, FaceRate.AsFrameTime(TimeSeconds), EAnimInterpolationType::Linear);
                }

                float AdditiveYaw = 0.0f;
                float AdditivePitch = 0.0f;
                float AdditiveRoll = 0.0f;

                if (TimeSeconds >= RangeStart && TimeSeconds <= RangeEnd && RangeDur > 0.0)
                {
                    const double RelTime = TimeSeconds - RangeStart;
                    const double Lead = FMath::Min(0.25, RangeDur * 0.15);
                    double Envelope = 1.0;
                    if (RelTime < Lead && Lead > 0.0)
                    {
                        Envelope = RelTime / Lead;
                    }
                    else if (RelTime > (RangeDur - Lead) && Lead > 0.0)
                    {
                        Envelope = (RangeDur - RelTime) / Lead;
                    }
                    Envelope = FMath::Clamp(Envelope, 0.0, 1.0);
                    Envelope = Envelope * Envelope * (3.0 - 2.0 * Envelope);

                    for (const FMHPDChannelInstruction& Inst : HeadInstructions)
                    {
                        const float W = Inst.Weight * BoneDistWeight * static_cast<float>(Envelope);
                        if (Inst.BehaviorId == TEXT("head_turn_left"))
                        {
                            AdditiveYaw += 32.0f * W;
                        }
                        else if (Inst.BehaviorId == TEXT("head_turn_right"))
                        {
                            AdditiveYaw -= 32.0f * W;
                        }
                        else if (Inst.BehaviorId == TEXT("head_pitch_up"))
                        {
                            AdditivePitch += 20.0f * W;
                        }
                        else if (Inst.BehaviorId == TEXT("head_pitch_down"))
                        {
                            AdditivePitch -= 20.0f * W;
                        }
                        else if (Inst.BehaviorId == TEXT("head_tilt"))
                        {
                            AdditiveRoll += 18.0f * W;
                        }
                        else if (Inst.BehaviorId == TEXT("head_nod"))
                        {
                            const double Phase = (RangeDur > 0.0) ? (RelTime / RangeDur) * 4.0 * PI : 0.0;
                            AdditivePitch -= 22.0f * BoneDistWeight * static_cast<float>(FMath::Max(0.0, FMath::Sin(Phase)) * Envelope);
                        }
                        else if (Inst.BehaviorId == TEXT("head_shake"))
                        {
                            const double Phase = RelTime * 3.0 * 2.0 * PI;
                            AdditiveYaw += 18.0f * BoneDistWeight * static_cast<float>(FMath::Sin(Phase) * Envelope);
                        }
                    }
                }

                FQuat BaseRot = CurrentTransform.GetRotation();
                FQuat AdditiveRot = FRotator(AdditivePitch, AdditiveYaw, AdditiveRoll).Quaternion();
                FQuat CombinedRot = AdditiveRot * BaseRot;
                CombinedRot.Normalize();

                PositionKeys.Add(FVector3f(CurrentTransform.GetTranslation()));
                RotationKeys.Add(FQuat4f(CombinedRot));
                ScaleKeys.Add(FVector3f(CurrentTransform.GetScale3D()));
            }

            Controller.RemoveBoneTrack(BoneName, false);
            if (Controller.AddBoneCurve(BoneName, false))
            {
                Controller.SetBoneTrackKeys(BoneName, PositionKeys, RotationKeys, ScaleKeys, false);
            }
        }

        Controller.CloseBracket(false);

        FaceAnim->PostEditChange();
        FaceAnim->MarkPackageDirty();

        TArray<UPackage*> PackagesToSave;
        PackagesToSave.Add(FaceAnim->GetOutermost());
        FEditorFileUtils::PromptForCheckoutAndSave(PackagesToSave, /*bCheckDirty*/ false, /*bPromptToSave*/ false);

        UE_LOG(LogTemp, Log, TEXT("MHPD: Baked head motion onto %d bones for %d keys"), TargetBones.Num(), NumKeys);
    }

    // Builds a self-contained Level Sequence: dialogue audio + the MetaHuman Face
    // binding with a single skeletal animation track playing FaceAnim from frame 0.
    static void AddControlRigTrackToSequence(
        ULevelSequence* Sequence,
        UMovieScene* MovieScene,
        const FGuid& BodyBinding,
        USkeletalMeshComponent* BodyComponent,
        const FMHPDPerformancePlan* Plan,
        FFrameRate DisplayRate,
        FFrameNumber StartFrame,
        FFrameNumber EndFrame)
    {
        if (!Sequence || !MovieScene || !BodyBinding.IsValid() || !Plan)
        {
            return;
        }

        // Check for active head movement instructions in the plan
        bool bHasHeadInstruction = false;
        for (const FMHPDChannelInstruction& Inst : Plan->Instructions)
        {
            if (Inst.Channel == EMHPDPerformanceChannel::HeadMovement && !Inst.bPreserveOriginal && Inst.Weight > 0.0f)
            {
                bHasHeadInstruction = true;
                break;
            }
        }

        if (!bHasHeadInstruction)
        {
            return;
        }

        // Load MetaHuman_ControlRig blueprint / class
        const FString RigPath = TEXT("/Game/MetaHumans/Common/Common/MetaHuman_ControlRig.MetaHuman_ControlRig_C");
        UClass* ControlRigClass = StaticLoadClass(UControlRig::StaticClass(), nullptr, *RigPath);
        if (!ControlRigClass)
        {
            UE_LOG(LogTemp, Warning, TEXT("MHPD: Could not load MetaHuman_ControlRig from '%s'"), *RigPath);
            return;
        }

        UMovieSceneControlRigParameterTrack* RigTrack = Cast<UMovieSceneControlRigParameterTrack>(
            MovieScene->AddTrack(UMovieSceneControlRigParameterTrack::StaticClass(), BodyBinding));
        if (!RigTrack)
        {
            return;
        }

        RigTrack->SetDisplayName(LOCTEXT("ControlRigTrackName", "MetaHuman_ControlRig (Head Motion)"));

        UControlRig* ControlRig = NewObject<UControlRig>(RigTrack, ControlRigClass, TEXT("MetaHuman_ControlRig"), RF_Transactional);
        if (!ControlRig)
        {
            return;
        }

        ControlRig->SetObjectBinding(MakeShared<FControlRigObjectBinding>());
        ControlRig->Initialize();

        UMovieSceneSection* NewSection = RigTrack->CreateControlRigSection(StartFrame, ControlRig, true);
        UMovieSceneControlRigParameterSection* RigSection = Cast<UMovieSceneControlRigParameterSection>(NewSection);
        if (!RigSection)
        {
            return;
        }

        RigSection->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));

        // Discover head & neck control names on the Control Rig
        FName HeadCtrlName = NAME_None;
        FName NeckCtrlName = NAME_None;

        if (const URigHierarchy* Hierarchy = ControlRig->GetHierarchy())
        {
            Hierarchy->ForEach<FRigControlElement>([&](const FRigControlElement* Element)
            {
                const FString NameStr = Element->GetFName().ToString().ToLower();
                if (HeadCtrlName == NAME_None && (NameStr.Contains(TEXT("head_fk")) || NameStr == TEXT("head_ctrl") || NameStr == TEXT("head")))
                {
                    HeadCtrlName = Element->GetFName();
                }
                if (NeckCtrlName == NAME_None && (NameStr.Contains(TEXT("neck_01_fk")) || NameStr.Contains(TEXT("neck_01_ctrl")) || NameStr == TEXT("neck_01") || NameStr.Contains(TEXT("neck_fk"))))
                {
                    NeckCtrlName = Element->GetFName();
                }
                return true;
            });
        }

        if (HeadCtrlName == NAME_None)
        {
            HeadCtrlName = FName(TEXT("head_fk_ctrl"));
        }
        if (NeckCtrlName == NAME_None)
        {
            NeckCtrlName = FName(TEXT("neck_01_ctrl"));
        }

        // Timing frames
        const float RevisionStartSec = Plan->RevisionRange.StartSeconds;
        const float RevisionEndSec   = Plan->RevisionRange.EndSeconds;
        const float RangeDur         = FMath::Max(0.1f, RevisionEndSec - RevisionStartSec);

        const float EaseInSec  = FMath::Min(0.35f, RangeDur * 0.25f);
        const float EaseOutSec = FMath::Min(0.45f, RangeDur * 0.30f);

        const FFrameNumber FrameT0 = SecondsToFrame(DisplayRate, RevisionStartSec);
        const FFrameNumber FrameT1 = SecondsToFrame(DisplayRate, RevisionStartSec + EaseInSec);
        const FFrameNumber FrameT2 = SecondsToFrame(DisplayRate, RevisionEndSec - EaseOutSec);
        const FFrameNumber FrameT3 = SecondsToFrame(DisplayRate, RevisionEndSec);

        for (const FMHPDChannelInstruction& Inst : Plan->Instructions)
        {
            if (Inst.Channel != EMHPDPerformanceChannel::HeadMovement || Inst.bPreserveOriginal || Inst.Weight <= 0.0f)
            {
                continue;
            }

            FRotator TargetHeadRot = FRotator::ZeroRotator;
            // In MetaHuman ControlRig:
            // Yaw: +Yaw = Turn Right, -Yaw = Turn Left
            // Pitch: +Pitch = Look Up, -Pitch = Look Down
            // Roll: +Roll = Tilt Right, -Roll = Tilt Left
            if (Inst.BehaviorId == TEXT("head_turn_right"))
            {
                TargetHeadRot.Yaw = 22.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_turn_left"))
            {
                TargetHeadRot.Yaw = -22.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_pitch_up"))
            {
                TargetHeadRot.Pitch = 16.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_pitch_down"))
            {
                TargetHeadRot.Pitch = -16.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_tilt"))
            {
                TargetHeadRot.Roll = 14.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_nod"))
            {
                TargetHeadRot.Pitch = -14.0f * Inst.Weight;
            }
            else if (Inst.BehaviorId == TEXT("head_shake"))
            {
                TargetHeadRot.Yaw = 16.0f * Inst.Weight;
            }

            const FRotator TargetNeckRot = TargetHeadRot * 0.35f;
            const FRotator PrimaryHeadRot = TargetHeadRot * 0.65f;

            // Key Head control
            RigSection->AddTransformParameterKey(HeadCtrlName, StartFrame, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(HeadCtrlName, FrameT0, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(HeadCtrlName, FrameT1, FTransform(PrimaryHeadRot), EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(HeadCtrlName, FrameT2, FTransform(PrimaryHeadRot), EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(HeadCtrlName, FrameT3, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(HeadCtrlName, EndFrame, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);

            // Key Neck control for organic cervical spine curvature
            RigSection->AddTransformParameterKey(NeckCtrlName, StartFrame, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(NeckCtrlName, FrameT0, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(NeckCtrlName, FrameT1, FTransform(TargetNeckRot), EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(NeckCtrlName, FrameT2, FTransform(TargetNeckRot), EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(NeckCtrlName, FrameT3, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);
            RigSection->AddTransformParameterKey(NeckCtrlName, EndFrame, FTransform::Identity, EMovieSceneKeyInterpolation::SmartAuto);

            UE_LOG(LogTemp, Log, TEXT("MHPD: Added MetaHuman_ControlRig head motion keys on Body for '%s' (Controls: '%s', '%s', Target Yaw: %.1f, Pitch: %.1f, Roll: %.1f)"),
                *Inst.BehaviorId.ToString(), *HeadCtrlName.ToString(), *NeckCtrlName.ToString(), TargetHeadRot.Yaw, TargetHeadRot.Pitch, TargetHeadRot.Roll);
        }
    }

    // Shared by Phase 1 (baseline) and Phase 2 (acting takes) so every take lives
    // in its own clean, isolated sequence asset (one Level Sequence per take).
    ULevelSequence* BuildFaceLevelSequence(
        const FString& SequenceName,
        const FString& OutputDir,
        UAnimSequence* FaceAnim,
        USoundWave* SoundWave,
        const FText& AnimTrackLabel,
        UAnimSequence* BodyAnim = nullptr,
        const FMHPDPerformancePlan* Plan = nullptr)
    {
        if (!GEditor) return nullptr;

        UWorld* World = GEditor->GetEditorWorldContext().World();
        if (!World) return nullptr;

        const FString SeqPkgPath = FString::Printf(TEXT("%s/%s"), *OutputDir, *SequenceName);

        UPackage* Package = CreatePackage(*SeqPkgPath);
        if (!Package) return nullptr;

        ULevelSequence* Sequence = NewObject<ULevelSequence>(Package, *SequenceName, RF_Public | RF_Standalone | RF_Transactional);
        if (!Sequence) return nullptr;

        Sequence->Initialize();
        UMovieScene* MovieScene = Sequence->GetMovieScene();
        if (!MovieScene) return nullptr;

        const FFrameRate DisplayRate(30, 1);
        MovieScene->SetDisplayRate(DisplayRate);
        MovieScene->SetTickResolutionDirectly(DisplayRate);

        // Calculate playback range from audio duration (fall back to anim length)
        float SequenceDuration = 10.0f;
        if (SoundWave)
        {
            SequenceDuration = FMath::Max(1.0f, SoundWave->GetDuration());
        }
        else if (FaceAnim)
        {
            SequenceDuration = FMath::Max(1.0f, FaceAnim->GetPlayLength());
        }
        const FFrameNumber StartFrame = SecondsToFrame(DisplayRate, 0.0f);
        const FFrameNumber EndFrame   = SecondsToFrame(DisplayRate, SequenceDuration);
        MovieScene->SetPlaybackRange(StartFrame, EndFrame.Value - StartFrame.Value);

        // Add audio track
        if (SoundWave)
        {
            UMovieSceneAudioTrack* AudioTrack = MovieScene->AddTrack<UMovieSceneAudioTrack>();
            if (AudioTrack)
            {
                AudioTrack->SetDisplayName(LOCTEXT("AudioTrackName", "Dialogue Audio"));
                UMovieSceneAudioSection* AudioSection = Cast<UMovieSceneAudioSection>(AudioTrack->CreateNewSection());
                if (AudioSection)
                {
                    AudioSection->SetSound(SoundWave);
                    AudioSection->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
                    AudioTrack->AddSection(*AudioSection);
                }
            }
        }

        // Bind the MetaHuman actor
        AActor* MetaHumanActor = FindMetaHumanActor(World);
        USkeletalMeshComponent* FaceComponent = MetaHumanActor ? FindMetaHumanFaceComponent(MetaHumanActor) : nullptr;
        USkeletalMeshComponent* BodyComponent = MetaHumanActor ? FindMetaHumanBodyComponent(MetaHumanActor) : nullptr;

        if (MetaHumanActor && FaceComponent && FaceAnim)
        {
            FaceComponent->SetAnimationMode(EAnimationMode::AnimationCustomMode);

            if (BodyComponent && BodyAnim)
            {
                BodyComponent->SetAnimationMode(EAnimationMode::AnimationCustomMode);
                FaceComponent->AddTickPrerequisiteComponent(BodyComponent);
            }

            if (UAnimInstance* ExistingAnimInst = FaceComponent->GetAnimInstance())
            {
                ExistingAnimInst->StopAllMontages(0.0f);
            }

            // Possess the actor
            const FString SafeActorLabel = MakeAssetSafeName(MetaHumanActor->GetActorLabel());
            const FGuid ActorBinding = MovieScene->AddPossessable(SafeActorLabel, MetaHumanActor->GetClass());
            Sequence->BindPossessableObject(ActorBinding, *MetaHumanActor, World);

            // Possess the Body component as a child of Actor
            FGuid BodyBinding;
            if (BodyComponent)
            {
                const FString SafeBodyName = MakeAssetSafeName(BodyComponent->GetName());
                BodyBinding = MovieScene->AddPossessable(SafeBodyName, BodyComponent->GetClass());
                Sequence->BindPossessableObject(BodyBinding, *BodyComponent, MetaHumanActor);

                FMovieScenePossessable* BodyPossessable = MovieScene->FindPossessable(BodyBinding);
                if (BodyPossessable)
                {
                    BodyPossessable->SetParent(ActorBinding, MovieScene);
                }
            }

            // Possess the Face component as a child of Actor
            const FString SafeFaceName = MakeAssetSafeName(FaceComponent->GetName());
            const FGuid FaceBinding = MovieScene->AddPossessable(SafeFaceName, FaceComponent->GetClass());
            Sequence->BindPossessableObject(FaceBinding, *FaceComponent, MetaHumanActor);

            FMovieScenePossessable* FacePossessable = MovieScene->FindPossessable(FaceBinding);
            if (FacePossessable)
            {
                FacePossessable->SetParent(ActorBinding, MovieScene);
            }

            if (BodyAnim && BodyBinding.IsValid())
            {
                UMovieSceneSkeletalAnimationTrack* BodyAnimTrack = MovieScene->AddTrack<UMovieSceneSkeletalAnimationTrack>(BodyBinding);
                if (BodyAnimTrack)
                {
                    BodyAnimTrack->SetDisplayName(LOCTEXT("BodyAnimTrackName", "Body Micro-Behavior"));
                    UMovieSceneSection* BodySection = BodyAnimTrack->CreateNewSection();
                    if (UMovieSceneSkeletalAnimationSection* SkelBodySection = Cast<UMovieSceneSkeletalAnimationSection>(BodySection))
                    {
                        SkelBodySection->Params.Animation = BodyAnim;
                        SkelBodySection->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
                        BodyAnimTrack->AddSection(*SkelBodySection);
                    }
                }
            }

            // Add Control Rig procedural head/neck motion track to BodyComponent if plan specifies head motion
            if (BodyBinding.IsValid() && Plan)
            {
                AddControlRigTrackToSequence(Sequence, MovieScene, BodyBinding, BodyComponent, Plan, DisplayRate, StartFrame, EndFrame);
            }

            // Add the face animation track for this take
            UMovieSceneSkeletalAnimationTrack* AnimTrack = MovieScene->AddTrack<UMovieSceneSkeletalAnimationTrack>(FaceBinding);
            if (AnimTrack)
            {
                AnimTrack->SetDisplayName(AnimTrackLabel);

                // Add the facial performance animation for this take
                UMovieSceneSection* AnimSection = AnimTrack->CreateNewSection();
                if (UMovieSceneSkeletalAnimationSection* SkelAnimSection = Cast<UMovieSceneSkeletalAnimationSection>(AnimSection))
                {
                    SkelAnimSection->Params.Animation = FaceAnim;
                    SkelAnimSection->SetRange(TRange<FFrameNumber>(StartFrame, EndFrame));
                    AnimTrack->AddSection(*SkelAnimSection);
                }
            }
        }

        // Register the new asset
        FAssetRegistryModule::AssetCreated(Sequence);
        Package->MarkPackageDirty();
        Sequence->MarkPackageDirty();

        return Sequence;
    }

    bool CreateBaselineLevelSequence(const FString& TakeName, const FString& OutputDir)
    {
        // Load the generated assets from the Python run
        const FString AnimAssetPath  = FString::Printf(TEXT("%s/Anim_Baseline_Face.Anim_Baseline_Face"), *OutputDir);
        const FString AudioAssetPath = FString::Printf(TEXT("%s/DialogueAudio_Base.DialogueAudio_Base"), *OutputDir);

        UAnimSequence* AnimSequence = Cast<UAnimSequence>(StaticLoadObject(UAnimSequence::StaticClass(), nullptr, *AnimAssetPath));
        USoundWave*    SoundWave    = Cast<USoundWave>(StaticLoadObject(USoundWave::StaticClass(), nullptr, *AudioAssetPath));

        const FString SeqName = FString::Printf(TEXT("LS_%s"), *MakeAssetSafeName(TakeName));
        ULevelSequence* Sequence = BuildFaceLevelSequence(SeqName, OutputDir, AnimSequence, SoundWave, LOCTEXT("BaselineAnimTrack", "Baseline Face Animation"));
        if (!Sequence) return false;

        // Store reference for Phase 2
        ActiveBaselineSequence = Sequence;
        ActiveBaselineTakeName = TakeName;

        // Start a fresh take history for this baseline session, seeded with the
        // baseline itself so the director can always A/B back to it.
        TakeHistoryList.Reset();
        TSharedPtr<FGeneratedTakeInfo> BaselineTake = MakeShared<FGeneratedTakeInfo>();
        BaselineTake->TakeName     = TEXT("Baseline");
        BaselineTake->SequencePath = Sequence->GetPathName();
        BaselineTake->StatusText   = FString::Printf(TEXT("Baseline performance: %s"), *TakeName);
        TakeHistoryList.Add(BaselineTake);
        SelectedTake = BaselineTake;
        if (TakeHistoryComboBox.IsValid())
        {
            TakeHistoryComboBox->RefreshOptions();
            TakeHistoryComboBox->SetSelectedItem(BaselineTake);
        }

        // Open in Sequencer
        if (UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
        {
            AssetEditorSubsystem->OpenEditorForAsset(Sequence);
        }

        return true;
    }

    void SetBaselineStatus(const FString& Message, bool bIsError)
    {
        if (BaselineStatusText.IsValid())
        {
            BaselineStatusText->SetText(FText::FromString(Message));
            BaselineStatusText->SetColorAndOpacity(
                bIsError
                    ? FSlateColor(FLinearColor(1.0f, 0.4f, 0.4f))
                    : FSlateColor(FLinearColor(0.6f, 0.9f, 0.6f))
            );
        }
    }

    FReply OnOpenInSequencerClicked()
    {
        if (ActiveBaselineSequence.IsValid())
        {
            if (UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
            {
                AssetEditorSubsystem->OpenEditorForAsset(ActiveBaselineSequence.Get());
            }
        }
        return FReply::Handled();
    }

    // -------------------------------------------------------------------------
    // Phase 2 — Acting Direction Takes
    // -------------------------------------------------------------------------

    FReply OnGenerateAndCreateClicked()
    {
        OnGeneratePlanClicked();
        CreateActingTakeSequence();
        return FReply::Handled();
    }

    void CreateActingTakeSequence()
    {
        if (!bHasLastPlan)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(LOCTEXT("NeedPlan", "Generate a plan before adding an acting take."));
            }
            return;
        }

        // Resolve the baseline session — adopt an open Level Sequence if the panel
        // does not know one yet (e.g. after an editor restart).
        ULevelSequence* BaselineSequence = ActiveBaselineSequence.Get();
        if (!BaselineSequence && GEditor)
        {
            UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>();
            if (AssetEditorSubsystem)
            {
                for (UObject* Asset : AssetEditorSubsystem->GetAllEditedAssets())
                {
                    if (ULevelSequence* OpenSeq = Cast<ULevelSequence>(Asset))
                    {
                        BaselineSequence = OpenSeq;
                        ActiveBaselineSequence = OpenSeq;
                        if (TakeHistoryList.Num() == 0)
                        {
                            TSharedPtr<FGeneratedTakeInfo> BaselineTake = MakeShared<FGeneratedTakeInfo>();
                            BaselineTake->TakeName     = TEXT("Baseline");
                            BaselineTake->SequencePath = OpenSeq->GetPathName();
                            BaselineTake->StatusText   = FString::Printf(TEXT("Adopted open sequence '%s' as baseline."), *OpenSeq->GetName());
                            TakeHistoryList.Add(BaselineTake);
                        }
                        break;
                    }
                }
            }
        }

        if (!BaselineSequence)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(LOCTEXT("NoBaseline", "No baseline take found. Generate a baseline first (Phase 1) or open a take in Sequencer."));
            }
            return;
        }

        if (!GEditor) return;

        const float RangeStart = FMath::Max(0.0f, ParseFloatTextBox(RangeStartTextBox, 0.0f));
        const float RangeEnd   = ParseFloatTextBox(RangeEndTextBox, 10.0f);

        // -------------------------------------------------------------------------
        // Generate the modified AnimSequence via Python (duplicates baseline + keys curves)
        // -------------------------------------------------------------------------
        IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
        if (!PythonPlugin)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(LOCTEXT("NoPython", "Error: PythonScriptPlugin unavailable."));
            }
            return;
        }

        // Folder holding this baseline session's assets.
        // Extract the actual parent package folder path (e.g. /Game/MHPD/Take_001)
        FString OutputDir;
        if (BaselineSequence)
        {
            OutputDir = FPackageName::GetLongPackagePath(BaselineSequence->GetOutermost()->GetName());
        }
        if (OutputDir.IsEmpty() || OutputDir == TEXT("/Game") || OutputDir == TEXT("/Game/MHPD"))
        {
            FString FolderName = ActiveBaselineTakeName;
            if (FolderName.StartsWith(TEXT("LS_")))
            {
                FolderName.RightChopInline(3);
            }
            FolderName = MakeAssetSafeName(FolderName);
            OutputDir = FString::Printf(TEXT("/Game/MHPD/%s"), *FolderName);
        }

        const FString TakeAnimName = FString::Printf(TEXT("Anim_%s"), *MakeAssetSafeName(LastGeneratedTakeName));
        const FString BaselineAnimPath = FString::Printf(TEXT("%s/Anim_Baseline_Face"), *OutputDir);

        // Serialize the interpreted plan to a JSON file so Python executes the
        // SAME plan the panel displays — one interpreter, no second keyword
        // parse, and no shell-escaping of free-form director text (apostrophes,
        // newlines, trailing backslashes) through the Python command line.
        FString PlanFilePath;
        if (UMHPDPerformanceDirectorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UMHPDPerformanceDirectorSubsystem>())
        {
            const FString PlanJson = Subsystem->ExportPlanToJson(LastPlan);
            const FString PlanDir = FPaths::ConvertRelativePathToFull(FPaths::ProjectSavedDir() / TEXT("MHPD"));
            IFileManager::Get().MakeDirectory(*PlanDir, true);
            PlanFilePath = PlanDir / TEXT("last_plan.json");
            if (!FFileHelper::SaveStringToFile(PlanJson, *PlanFilePath, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
            {
                PlanFilePath.Reset();
            }
        }

        // Resolve the Body Library selection BEFORE baking: the body animation's
        // shared bone tracks (root..spine..neck..head) are baked into the take so
        // the head follows the body. The "Preserve body animation" lock vetoes the
        // dropdown too — a locked channel must not change however it was requested.
        FString BodyAnimPath;
        if (SelectedBodyOption.IsValid() && !SelectedBodyOption->StartsWith(TEXT("N/A")))
        {
            if (IsChecked(BodyAnimationCheckBox))
            {
                UE_LOG(LogTemp, Log, TEXT("MHPD: Body animation channel is locked - ignoring Body Library selection '%s'"), **SelectedBodyOption);
            }
            else
            {
                BodyAnimPath = *SelectedBodyOption;
            }
        }

        const FString PythonCmd = FString::Printf(
            TEXT("import importlib, generate_acting_take; importlib.reload(generate_acting_take); generate_acting_take.create_acting_take(r'%s', '%s', r'%s', range_start=%.3f, range_end=%.3f, plan_path=r'%s')"),
            *BaselineAnimPath,
            *TakeAnimName,
            *OutputDir,
            RangeStart,
            RangeEnd,
            *PlanFilePath
        );

        PythonPlugin->ExecPythonCommand(*PythonCmd);

        const FString NewAnimAssetPath = FString::Printf(TEXT("%s/%s.%s"), *OutputDir, *TakeAnimName, *TakeAnimName);
        UAnimSequence* ModifiedAnimSeq = Cast<UAnimSequence>(StaticLoadObject(UAnimSequence::StaticClass(), nullptr, *NewAnimAssetPath));

        if (!ModifiedAnimSeq)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(LOCTEXT("AnimFail", "Failed to load modified acting take AnimSequence. Check Output Log."));
            }
            return;
        }

        // Reuse the baseline's dialogue audio so every take plays synced audio
        const FString AudioAssetPath = FString::Printf(TEXT("%s/DialogueAudio_Base.DialogueAudio_Base"), *OutputDir);
        USoundWave* SoundWave = Cast<USoundWave>(StaticLoadObject(USoundWave::StaticClass(), nullptr, *AudioAssetPath));

        // The body animation gets its own Sequencer track on the Body binding (so
        // the body performs the gesture), AND its bone tracks are baked into the
        // face take so the head travels with it instead of tearing away.
        UAnimSequence* SelectedBodyAnim = BodyAnimPath.IsEmpty()
            ? nullptr
            : Cast<UAnimSequence>(StaticLoadObject(UAnimSequence::StaticClass(), nullptr, *BodyAnimPath));

        // If the director selected a gesture from the Body Library, attach it;
        // otherwise, head motion is evaluated cleanly via the native HeadControlSwitch/HeadYaw
        // curves on the Face AnimSequence without competing bone synthesizers.
        UAnimSequence* BodyTrackAnim = SelectedBodyAnim;

        // One Level Sequence per take: every acting take gets its own dedicated,
        // self-contained sequence. A/B comparison is switching sequences from the
        // take dropdown — no track blending, muting, or row juggling involved.
        const FString TakeSeqName = FString::Printf(TEXT("LS_%s"), *MakeAssetSafeName(LastGeneratedTakeName));
        ULevelSequence* TakeSequence = BuildFaceLevelSequence(TakeSeqName, OutputDir, ModifiedAnimSeq, SoundWave, FText::FromString(LastGeneratedTakeName), BodyTrackAnim, &LastPlan);
        if (!TakeSequence)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(LOCTEXT("TakeSeqFail", "Failed to create the acting take Level Sequence. Check Output Log."));
            }
            return;
        }

        // Register in history
        TSharedPtr<FGeneratedTakeInfo> NewTake = MakeShared<FGeneratedTakeInfo>();
        NewTake->TakeName     = LastGeneratedTakeName;
        NewTake->SequencePath = TakeSequence->GetPathName();
        NewTake->StatusText   = FString::Printf(TEXT("Created take sequence '%s'. Switch between Baseline and takes with the dropdown."), *TakeSeqName);
        NewTake->OutputText   = PlanTextBox.IsValid() ? PlanTextBox->GetText().ToString() : FString();
        TakeHistoryList.Add(NewTake);
        SelectedTake = NewTake;

        if (TakeHistoryComboBox.IsValid())
        {
            TakeHistoryComboBox->RefreshOptions();
            TakeHistoryComboBox->SetSelectedItem(NewTake);
        }

        if (TakeStatusText.IsValid())
        {
            TakeStatusText->SetText(FText::FromString(NewTake->StatusText));
        }

        // Open the new take in Sequencer for immediate preview
        if (UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
        {
            AssetEditorSubsystem->OpenEditorForAsset(TakeSequence);
        }

        GEditor->RedrawAllViewports();
    }

    FReply OnClearFollowUpClicked()
    {
        if (FollowUpTextBox.IsValid())
        {
            FollowUpTextBox->SetText(FText::GetEmpty());
        }
        return FReply::Handled();
    }

    FReply OnGeneratePlanClicked()
    {
        if (!GEditor)
        {
            PlanTextBox->SetText(LOCTEXT("NoEditor", "GEditor is unavailable."));
            return FReply::Handled();
        }

        UMHPDPerformanceDirectorSubsystem* Subsystem = GEditor->GetEditorSubsystem<UMHPDPerformanceDirectorSubsystem>();
        if (!Subsystem)
        {
            PlanTextBox->SetText(LOCTEXT("NoSubsystem", "MetaHuman Performance Director subsystem is unavailable."));
            return FReply::Handled();
        }

        const FString SourceTake = SourceTakeTextBox.IsValid()
            ? SourceTakeTextBox->GetText().ToString().TrimStartAndEnd()
            : TEXT("Current Sequencer Take");

        FMHPDRevisionRange RevisionRange;
        RevisionRange.StartSeconds = FMath::Max(0.0f, ParseFloatTextBox(RangeStartTextBox, 0.0f));
        RevisionRange.EndSeconds   = ParseFloatTextBox(RangeEndTextBox, 10.0f);
        if (RevisionRange.EndSeconds <= RevisionRange.StartSeconds)
        {
            RevisionRange.EndSeconds = RevisionRange.StartSeconds + 1.0f;
        }

        FString DirectionText = DirectionTextBox.IsValid()
            ? DirectionTextBox->GetText().ToString().TrimStartAndEnd()
            : FString();

        const FString FollowUpText = FollowUpTextBox.IsValid()
            ? FollowUpTextBox->GetText().ToString().TrimStartAndEnd()
            : FString();

        if (!FollowUpText.IsEmpty())
        {
            DirectionText += TEXT("\nFollow-up note: ");
            DirectionText += FollowUpText;
        }

        const FMHPDPerformancePlan Plan = Subsystem->CreatePlanFromDirection(
            DirectionText,
            SourceTake.IsEmpty() ? TEXT("Current Sequencer Take") : SourceTake,
            Intensity,
            RevisionRange,
            BuildLockedChannels()
        );

        const FString Json              = Subsystem->ExportPlanToJson(Plan);
        const FString GeneratedTakeName = BuildTakeName(Plan);
        LastPlan              = Plan;
        LastGeneratedTakeName = GeneratedTakeName;
        bHasLastPlan          = true;

        if (TakeStatusText.IsValid())
        {
            TakeStatusText->SetText(FText::FromString(FString::Printf(
                TEXT("Plan generated: %s\nRevision range: %.2fs to %.2fs"),
                *GeneratedTakeName,
                Plan.RevisionRange.StartSeconds,
                Plan.RevisionRange.EndSeconds
            )));
        }

        PlanTextBox->SetText(FText::FromString(FormatPlanForDisplay(Plan, GeneratedTakeName, Json)));
        return FReply::Handled();
    }

    // -------------------------------------------------------------------------
    // Helper UI builders
    // -------------------------------------------------------------------------

    TSharedRef<SWidget> MakeTextInputRow(TSharedPtr<SEditableTextBox>& OutTextBox, const FText& Label, const FText& InitialText, float Width = 0.0f)
    {
        TSharedRef<SWidget> TextBox = SAssignNew(OutTextBox, SEditableTextBox).Text(InitialText);
        if (Width > 0.0f)
        {
            TextBox = SNew(SBox).WidthOverride(Width)[TextBox];
        }
        return SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[SNew(STextBlock).Text(Label)]
            + SVerticalBox::Slot().AutoHeight()[TextBox];
    }

    TSharedRef<SWidget> MakeLockColumn(bool bFirstColumn)
    {
        if (bFirstColumn)
        {
            return SNew(SVerticalBox)
                + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(DialogueAudioCheckBox, LOCTEXT("DialogueAudioLock", "Dialogue audio"), true)]
                + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(LipSyncCheckBox, LOCTEXT("LipSyncLock", "Lip synchronization"), true)]
                + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(TimingCheckBox, LOCTEXT("TimingLock", "Timing"), false)];
        }
        return SNew(SVerticalBox)
            + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(FacialAnimationCheckBox, LOCTEXT("FacialAnimationLock", "Facial animation"), false)]
            + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(GazeCheckBox, LOCTEXT("GazeLock", "Gaze / eye contact"), false)]
            + SVerticalBox::Slot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, 4.0f)[MakeLockRow(BodyAnimationCheckBox, LOCTEXT("BodyAnimationLock", "Body animation"), false)];
    }

    TSharedRef<SWidget> MakeLockRow(TSharedPtr<SCheckBox>& OutCheckBox, const FText& Label, bool bCheckedByDefault)
    {
        return SNew(SHorizontalBox)
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center)
            [
                SAssignNew(OutCheckBox, SCheckBox)
                .IsChecked(bCheckedByDefault ? ECheckBoxState::Checked : ECheckBoxState::Unchecked)
            ]
            + SHorizontalBox::Slot().AutoWidth().VAlign(VAlign_Center).Padding(8.0f, 0.0f, 0.0f, 0.0f)
            [
                SNew(STextBlock).Text(Label)
            ];
    }

    // -------------------------------------------------------------------------
    // Helper logic
    // -------------------------------------------------------------------------

    FText GetIntensityText() const
    {
        return FText::Format(LOCTEXT("IntensityValue", "Performance size: {0}%"), FText::AsNumber(FMath::RoundToInt(Intensity * 100.0f)));
    }

    void OnIntensityChanged(float NewValue)
    {
        Intensity = NewValue;
        if (IntensityLabel.IsValid())
        {
            IntensityLabel->SetText(GetIntensityText());
        }
    }

    TSharedRef<SWidget> GenerateTakeHistoryRow(TSharedPtr<FGeneratedTakeInfo> Item)
    {
        return SNew(STextBlock).Text(FText::FromString(Item.IsValid() ? Item->TakeName : TEXT("None")));
    }

    void OnTakeSelectionChanged(TSharedPtr<FGeneratedTakeInfo> NewSelection, ESelectInfo::Type SelectInfo)
    {
        SelectedTake = NewSelection;
        if (SelectedTake.IsValid())
        {
            if (TakeStatusText.IsValid() && !SelectedTake->StatusText.IsEmpty())
            {
                TakeStatusText->SetText(FText::FromString(SelectedTake->StatusText));
            }
            if (PlanTextBox.IsValid() && !SelectedTake->OutputText.IsEmpty())
            {
                PlanTextBox->SetText(FText::FromString(SelectedTake->OutputText));
            }

            // User-driven selection switches Sequencer to that take's Level Sequence.
            // (Programmatic SetSelectedItem passes ESelectInfo::Direct and the
            // generation path opens the sequence itself — skip double-opening.)
            if (SelectInfo != ESelectInfo::Direct)
            {
                OpenTakeSequence(SelectedTake);
            }
        }
    }

    void OpenTakeSequence(const TSharedPtr<FGeneratedTakeInfo>& Take)
    {
        if (!Take.IsValid() || Take->SequencePath.IsEmpty() || !GEditor)
        {
            return;
        }

        ULevelSequence* Sequence = Cast<ULevelSequence>(StaticLoadObject(ULevelSequence::StaticClass(), nullptr, *Take->SequencePath));
        if (!Sequence)
        {
            if (TakeStatusText.IsValid())
            {
                TakeStatusText->SetText(FText::FromString(FString::Printf(TEXT("Could not load take sequence: %s"), *Take->SequencePath)));
            }
            return;
        }

        if (UAssetEditorSubsystem* AssetEditorSubsystem = GEditor->GetEditorSubsystem<UAssetEditorSubsystem>())
        {
            AssetEditorSubsystem->OpenEditorForAsset(Sequence);
        }
    }

    FText GetSelectedTakeText() const
    {
        return SelectedTake.IsValid() ? FText::FromString(SelectedTake->TakeName) : LOCTEXT("NoTakeSelected", "None generated");
    }

    bool CanRemoveSelectedTake() const
    {
        return SelectedTake.IsValid() && TakeHistoryList.Num() > 0;
    }

    FReply OnRemoveTakeClicked()
    {
        if (!SelectedTake.IsValid())
        {
            return FReply::Handled();
        }

        const int32 Index = TakeHistoryList.IndexOfByKey(SelectedTake);
        if (Index != INDEX_NONE)
        {
            const FString RemovedName = SelectedTake->TakeName;
            TakeHistoryList.RemoveAt(Index);

            // Select adjacent take or reset
            TSharedPtr<FGeneratedTakeInfo> NewSelection = nullptr;
            if (TakeHistoryList.Num() > 0)
            {
                const int32 NewIndex = FMath::Clamp(Index > 0 ? Index - 1 : 0, 0, TakeHistoryList.Num() - 1);
                NewSelection = TakeHistoryList[NewIndex];
            }

            SelectedTake = NewSelection;

            if (TakeHistoryComboBox.IsValid())
            {
                TakeHistoryComboBox->RefreshOptions();
                TakeHistoryComboBox->SetSelectedItem(SelectedTake);
            }

            if (SelectedTake.IsValid())
            {
                if (TakeStatusText.IsValid())
                {
                    TakeStatusText->SetText(FText::FromString(FString::Printf(TEXT("Removed take '%s'. Active take is now '%s'."), *RemovedName, *SelectedTake->TakeName)));
                }
                OpenTakeSequence(SelectedTake);
            }
            else
            {
                if (TakeStatusText.IsValid())
                {
                    TakeStatusText->SetText(FText::FromString(FString::Printf(TEXT("Removed take '%s'. No takes remaining in dropdown."), *RemovedName)));
                }
                if (PlanTextBox.IsValid())
                {
                    PlanTextBox->SetText(FText::GetEmpty());
                }
            }
        }

        return FReply::Handled();
    }

    FString BuildTakeName(const FMHPDPerformancePlan& Plan) const
    {
        const FString PrimaryIntent = Plan.MatchedInterpretations.Num() > 0
            ? Plan.MatchedInterpretations[0]
            : TEXT("directed_revision");
        const FString ShortPlanId = Plan.PlanId.ToString().Left(8);
        return FString::Printf(TEXT("ALT_%s_%03d_%s"), *MakeTakeToken(PrimaryIntent), FMath::RoundToInt(Plan.Intensity * 100.0f), *ShortPlanId);
    }

    TArray<FString> BuildLockedChannels() const
    {
        TArray<FString> LockedChannels;
        if (IsChecked(DialogueAudioCheckBox))  LockedChannels.Add(TEXT("dialogue_audio"));
        if (IsChecked(LipSyncCheckBox))        LockedChannels.Add(TEXT("lip_sync"));
        if (IsChecked(FacialAnimationCheckBox)) LockedChannels.Add(TEXT("facial_animation"));
        if (IsChecked(GazeCheckBox))           LockedChannels.Add(TEXT("gaze"));
        if (IsChecked(BodyAnimationCheckBox))  LockedChannels.Add(TEXT("body_animation"));
        if (IsChecked(TimingCheckBox))         LockedChannels.Add(TEXT("timing"));
        return LockedChannels;
    }

    FString FormatPlanForDisplay(const FMHPDPerformancePlan& Plan, const FString& GeneratedTakeName, const FString& Json) const
    {
        FString Output;
        Output += FString::Printf(TEXT("Acting take: %s\n"), *GeneratedTakeName);
        Output += FString::Printf(TEXT("Source take: %s\n"), *Plan.SourceTake);
        Output += FString::Printf(TEXT("Timeline region: %.2fs - %.2fs\n"), Plan.RevisionRange.StartSeconds, Plan.RevisionRange.EndSeconds);
        Output += FString::Printf(TEXT("Performance size: %d%%\n\n"), FMath::RoundToInt(Plan.Intensity * 100.0f));

        Output += TEXT("Interpreted director intent:\n");
        for (const FString& Interpretation : Plan.MatchedInterpretations)
        {
            Output += FString::Printf(TEXT("- %s\n"), *Interpretation);
        }

        Output += TEXT("\nPreserved channels:\n");
        if (Plan.LockedChannels.Num() == 0) Output += TEXT("- None\n");
        for (const FString& LockedChannel : Plan.LockedChannels)
        {
            Output += FString::Printf(TEXT("- %s\n"), *LockedChannel);
        }

        Output += TEXT("\nChannel plan:\n");
        for (const FMHPDChannelInstruction& Instruction : Plan.Instructions)
        {
            Output += FString::Printf(
                TEXT("- %s | %s | weight %.2f | timing %.2fs | %s\n  %s\n"),
                *ChannelToString(Instruction.Channel),
                *Instruction.BehaviorId.ToString(),
                Instruction.Weight,
                Instruction.TimingOffsetSeconds,
                Instruction.bPreserveOriginal ? TEXT("preserve original") : TEXT("additive layer"),
                *Instruction.Description
            );
        }

        Output += TEXT("\nEditable output:\n");
        Output += TEXT("- Baseline performance remains unchanged.\n");
        Output += TEXT("- Acting take generated as an isolated Level Sequence with procedural Control Rig and RigLogic curves.\n");
        Output += TEXT("- Instant A/B comparison available via the Acting Takes dropdown.\n");
        Output += TEXT("\nStructured JSON:\n");
        Output += Json;
        return Output;
    }

    // -------------------------------------------------------------------------
    // Voice recording
    // -------------------------------------------------------------------------

    FText GetRecordVoiceButtonText() const
    {
        if (VoiceProcess.IsValid() && VoiceProcess->IsRunning())
        {
            return LOCTEXT("ListeningRecording", "Listening... (Release to stop)");
        }
        return LOCTEXT("StartRecording", "Hold to Talk");
    }

    void OnRecordVoicePressed()
    {
        if (VoiceProcess.IsValid() && VoiceProcess->IsRunning()) return;
        if (DirectionTextBox.IsValid())
        {
            DirectionTextBox->SetText(FText::GetEmpty());
        }

        FString PythonExe   = TEXT("C:\\Users\\david\\AppData\\Local\\Microsoft\\WindowsApps\\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\\python.exe");
        FString ScriptPath  = FPaths::Combine(FPaths::ProjectDir(), TEXT("../../MetaHumanPerformanceDirector/prototype/transcribe_voice.py"));
        FPaths::CollapseRelativeDirectories(ScriptPath);

        VoiceProcess = MakeShareable(new FInteractiveProcess(PythonExe, FString::Printf(TEXT("\"%s\""), *ScriptPath), true));
        VoiceProcess->OnOutput().BindRaw(this, &SMHPDDirectorPanel::OnVoiceProcessOutput);
        VoiceProcess->OnCompleted().BindRaw(this, &SMHPDDirectorPanel::OnVoiceProcessCompleted);
        VoiceProcess->Launch();
    }

    void OnRecordVoiceReleased()
    {
        if (VoiceProcess.IsValid() && VoiceProcess->IsRunning())
        {
            VoiceProcess->SendWhenReady(TEXT("\n"));
        }
    }

    void OnVoiceProcessOutput(const FString& Output)
    {
        AsyncTask(ENamedThreads::GameThread, [this, Output]()
        {
            if (Output.StartsWith(TEXT("MHPD_VOICE_RESULT: ")))
            {
                if (DirectionTextBox.IsValid())
                    DirectionTextBox->SetText(FText::FromString(Output.Mid(19).TrimStartAndEnd()));
            }
            else if (Output.StartsWith(TEXT("MHPD_VOICE_STATUS: ")))
            {
                if (DirectionTextBox.IsValid())
                    DirectionTextBox->SetText(FText::FromString(Output.Mid(19).TrimStartAndEnd()));
            }
            else if (Output.StartsWith(TEXT("MHPD_VOICE_ERROR: ")))
            {
                if (DirectionTextBox.IsValid())
                    DirectionTextBox->SetText(FText::FromString(FString::Printf(TEXT("Error: %s"), *Output.Mid(18).TrimStartAndEnd())));
            }
        });
    }

    void ScanBodyLibrary()
    {
        BodyLibraryOptions.Reset();
        TSharedPtr<FString> OptionNA = MakeShared<FString>(TEXT("N/A (No Body Motion)"));
        BodyLibraryOptions.Add(OptionNA);
        SelectedBodyOption = OptionNA;

        if (FModuleManager::Get().IsModuleLoaded(TEXT("AssetRegistry")))
        {
            FAssetRegistryModule& AssetRegistryModule = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry"));
            IAssetRegistry& AssetRegistry = AssetRegistryModule.Get();

            FARFilter Filter;
            Filter.PackagePaths.Add(TEXT("/Game/MHPD/BodyLibrary"));
            Filter.ClassPaths.Add(UAnimSequence::StaticClass()->GetClassPathName());
            Filter.bRecursivePaths = true;

            TArray<FAssetData> AssetList;
            AssetRegistry.GetAssets(Filter, AssetList);

            for (const FAssetData& AssetData : AssetList)
            {
                BodyLibraryOptions.Add(MakeShared<FString>(AssetData.GetObjectPathString()));
            }
        }

        if (BodyLibraryComboBox.IsValid())
        {
            BodyLibraryComboBox->RefreshOptions();
            BodyLibraryComboBox->SetSelectedItem(SelectedBodyOption);
        }
    }

    TSharedRef<SWidget> GenerateBodyLibraryRow(TSharedPtr<FString> Option)
    {
        FString DisplayName = Option.IsValid() ? *Option : TEXT("N/A (No Body Motion)");
        int32 LastSlashIdx = -1;
        if (DisplayName.FindLastChar('/', LastSlashIdx))
        {
            DisplayName = DisplayName.Mid(LastSlashIdx + 1);
        }
        return SNew(STextBlock).Text(FText::FromString(DisplayName));
    }

    FReply OnScanBodyLibraryClicked()
    {
        ScanBodyLibrary();
        return FReply::Handled();
    }

    void OnBodyLibrarySelectionChanged(TSharedPtr<FString> NewSelection, ESelectInfo::Type SelectInfo)
    {
        if (NewSelection.IsValid())
        {
            SelectedBodyOption = NewSelection;
        }
    }

    FText GetSelectedBodyLibraryText() const
    {
        if (SelectedBodyOption.IsValid())
        {
            FString DisplayName = *SelectedBodyOption;
            int32 LastSlashIdx = -1;
            if (DisplayName.FindLastChar('/', LastSlashIdx))
            {
                DisplayName = DisplayName.Mid(LastSlashIdx + 1);
            }
            return FText::FromString(DisplayName);
        }
        return LOCTEXT("NoBodySelected", "N/A (No Body Motion)");
    }

    void OnVoiceProcessCompleted(int32 ReturnCode, bool bCanceled)
    {
        AsyncTask(ENamedThreads::GameThread, [this, ReturnCode, bCanceled]()
        {
            VoiceProcess.Reset();
        });
    }

private: 
};

// ============================================================================
//  Module
// ============================================================================
class FMetaHumanPerformanceDirectorModule : public IModuleInterface
{
public:
    virtual void StartupModule() override
    {
        FGlobalTabmanager::Get()->RegisterNomadTabSpawner(
            MHPDTabName,
            FOnSpawnTab::CreateRaw(this, &FMetaHumanPerformanceDirectorModule::SpawnDirectorTab)
        )
        .SetDisplayName(LOCTEXT("TabTitle", "Performance Director"))
        .SetMenuType(ETabSpawnerMenuType::Hidden);

        UToolMenus::RegisterStartupCallback(
            FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FMetaHumanPerformanceDirectorModule::RegisterMenus)
        );
    }

    virtual void ShutdownModule() override
    {
        UToolMenus::UnRegisterStartupCallback(this);
        UToolMenus::UnregisterOwner(this);
        FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(MHPDTabName);
    }

private:
    TSharedRef<SDockTab> SpawnDirectorTab(const FSpawnTabArgs& Args)
    {
        return SNew(SDockTab)
            .TabRole(ETabRole::NomadTab)
            [
                SNew(SMHPDDirectorPanel)
            ];
    }

    void RegisterMenus()
    {
        FToolMenuOwnerScoped OwnerScoped(this);
        UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Window");
        if (!Menu) return;

        FToolMenuSection& Section = Menu->FindOrAddSection("WindowLayout");
        Section.AddMenuEntry(
            "OpenMetaHumanPerformanceDirector",
            LOCTEXT("MenuLabel", "MetaHuman Performance Director"),
            LOCTEXT("MenuTooltip", "Open the MetaHuman Performance Director panel."),
            FSlateIcon(),
            FUIAction(FExecuteAction::CreateRaw(this, &FMetaHumanPerformanceDirectorModule::OpenDirectorTab))
        );
    }

    void OpenDirectorTab()
    {
        FGlobalTabmanager::Get()->TryInvokeTab(MHPDTabName);
    }
};

IMPLEMENT_MODULE(FMetaHumanPerformanceDirectorModule, MetaHumanPerformanceDirector)

#undef LOCTEXT_NAMESPACE