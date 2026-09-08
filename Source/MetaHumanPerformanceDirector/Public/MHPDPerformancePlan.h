#pragma once

#include "CoreMinimal.h"
#include "MHPDPerformancePlan.generated.h"

UENUM(BlueprintType)
enum class EMHPDPerformanceChannel : uint8
{
    FacialExpression,
    Gaze,
    HeadMovement,
    Gesture,
    BodyPosture,
    ReactionTiming,
    Pauses,
    VoiceDelivery
};

USTRUCT(BlueprintType)
struct FMHPDRevisionRange
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    float StartSeconds = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    float EndSeconds = 0.0f;
};

USTRUCT(BlueprintType)
struct FMHPDChannelInstruction
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    EMHPDPerformanceChannel Channel = EMHPDPerformanceChannel::FacialExpression;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FName BehaviorId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FString Description;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float Weight = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    bool bPreserveOriginal = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    float TimingOffsetSeconds = 0.0f;
};

USTRUCT(BlueprintType)
struct FMHPDPerformancePlan
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FGuid PlanId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FString SourceTake;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FString DirectionText;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FMHPDRevisionRange RevisionRange;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float Intensity = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float FramingScale = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float FacialNuance = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float PhysicalAction = 0.5f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1.0"))
    float SubtextSuppression = 0.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director", meta = (ClampMin = "0.0", ClampMax = "1000.0"))
    float PreparationOffsetMs = 250.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    bool bFallback = false;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    TArray<FString> MatchedInterpretations;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    TArray<FString> LockedChannels;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    TArray<FMHPDChannelInstruction> Instructions;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    FString EditableOutputTarget = TEXT("sequencer_control_rig_layers");

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "MetaHuman Performance Director")
    bool bNonDestructive = true;
};