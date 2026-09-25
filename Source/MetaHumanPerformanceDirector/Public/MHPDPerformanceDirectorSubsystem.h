// Copyright (c) 2026 David Cobbins / Frontier Mindworks. All Rights Reserved.
// MetaHuman Performance Director (MHPD) — Architected & Developed by David Cobbins.

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
        const TArray<FString>& LockedChannels,
        float FramingScale = 0.5f,
        float FacialNuance = 0.5f,
        float PhysicalAction = 0.5f,
        float SubtextSuppression = 0.0f,
        float PreparationOffsetMs = 250.0f
    ) const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director")
    void AutoCalibrateDials(
        const FString& DirectionText,
        float& OutFramingScale,
        float& OutFacialNuance,
        float& OutPhysicalAction,
        float& OutSubtextSuppression,
        float& OutPreparationOffsetMs
    ) const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director")
    FString ExportPlanToJson(const FMHPDPerformancePlan& Plan) const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    EMHPDDirectorialEngine GetDirectorialEngine() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    void SetDirectorialEngine(EMHPDDirectorialEngine NewEngine);

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    EMHPDRenderQuality GetRenderQuality() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    void SetRenderQuality(EMHPDRenderQuality NewQuality);

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    bool IsLocalSLMModelAvailable() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    FString GetLocalSLMModelPath() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    FString GetLastActiveSessionPath() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    void SetLastActiveSessionPath(const FString& NewPath);

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    FString GetCustomTakeRootPath() const;

    UFUNCTION(BlueprintCallable, Category = "MetaHuman Performance Director|Settings")
    void SetCustomTakeRootPath(const FString& NewRoot);

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

