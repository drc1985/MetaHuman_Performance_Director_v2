#pragma once

#include "CoreMinimal.h"
#include "EditorSubsystem.h"
#include "MHPDPerformancePlan.h"
#include "MHPDPerformanceDirectorSubsystem.generated.h"

UCLASS()
class METAHUMANPERFORMANCEDIRECTOR_API UMHPDPerformanceDirectorSubsystem : public UEditorSubsystem
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director")
    FMHPDPerformancePlan CreatePlanFromDirection(
        const FString& DirectionText,
        const FString& SourceTake,
        float Intensity,
        FMHPDRevisionRange RevisionRange,
        const TArray<FString>& LockedChannels
    ) const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director")
    FString ExportPlanToJson(const FMHPDPerformancePlan& Plan) const;

private:
    void AddInstruction(
        FMHPDPerformancePlan& Plan,
        EMHPDPerformanceChannel Channel,
        const FName BehaviorId,
        const FString& Description,
        float BaseWeight,
        float TimingOffsetSeconds = 0.0f
    ) const;

    bool IsChannelLocked(EMHPDPerformanceChannel Channel, const TArray<FString>& LockedChannels) const;
};

