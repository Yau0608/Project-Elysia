using UnityEngine;
using UnityEditor;
using System.Text;
using System.IO;
using System.Collections.Generic;
using System.Linq;

public class AnimationClipExporter
{
    // --- OPTION 1: EXPORT SAMPLED DATA ---
    // The menu item will be under a new sub-menu "Assets/Export Animation"
    [MenuItem("Assets/Export Animation/To CSV (Sampled at Frame Rate)")]
    private static void ExportAnimationSampled()
    {
        AnimationClip clip = Selection.activeObject as AnimationClip;
        if (clip == null)
        {
            EditorUtility.DisplayDialog("Error", "Please select an AnimationClip to export.", "OK");
            return;
        }

        // Use the clip's frame rate for sampling
        float sampleRate = clip.frameRate;
        string filePath = Path.Combine(Application.dataPath, "..", clip.name + "_Sampled.csv");

        ExportClip(clip, filePath, sampleRate);
    }

    // --- OPTION 2: EXPORT KEYFRAMES ONLY ---
    [MenuItem("Assets/Export Animation/To CSV (Keyframes Only)")]
    private static void ExportKeyframes()
    {
        AnimationClip clip = Selection.activeObject as AnimationClip;
        if (clip == null)
        {
            EditorUtility.DisplayDialog("Error", "Please select an AnimationClip to export.", "OK");
            return;
        }

        string filePath = Path.Combine(Application.dataPath, "..", clip.name + "_Keyframes.csv");
        ExportKeyframes(clip, filePath);
    }

    // This validation function enables the menu items only if an AnimationClip is selected.
    [MenuItem("Assets/Export Animation/To CSV (Sampled at Frame Rate)", true)]
    [MenuItem("Assets/Export Animation/To CSV (Keyframes Only)", true)]
    private static bool ValidateExportOptions()
    {
        return Selection.activeObject is AnimationClip;
    }

    // --- IMPLEMENTATION for SAMPLED EXPORT ---
    private static void ExportClip(AnimationClip clip, string filePath, float sampleRate)
    {
        StringBuilder sb = new StringBuilder();
        EditorCurveBinding[] curveBindings = AnimationUtility.GetCurveBindings(clip);

        // Header Row
        sb.Append("Property,");
        float time = 0f;
        while (time <= clip.length)
        {
            sb.Append(time.ToString("F3") + ",");
            time += 1.0f / sampleRate;
        }
        sb.AppendLine();

        // Data Rows
        foreach (EditorCurveBinding binding in curveBindings)
        {
            AnimationCurve curve = AnimationUtility.GetEditorCurve(clip, binding);
            // Clean up the property name for better readability
            string propertyName = GetFriendlyPropertyName(binding);
            sb.Append(propertyName + ",");

            time = 0f;
            while (time <= clip.length)
            {
                float value = curve.Evaluate(time);
                sb.Append(value.ToString("F8") + ","); // Use "F8" for higher precision
                time += 1.0f / sampleRate;
            }
            sb.AppendLine();
        }

        WriteToFile(filePath, sb.ToString(), clip.name);
    }

    // --- IMPLEMENTATION for KEYFRAME-ONLY EXPORT ---
    private static void ExportKeyframes(AnimationClip clip, string filePath)
    {
        StringBuilder sb = new StringBuilder();
        EditorCurveBinding[] curveBindings = AnimationUtility.GetCurveBindings(clip);

        // Header: Property, Time, Value
        sb.AppendLine("Property,Time,Value");

        // Data Rows
        foreach (EditorCurveBinding binding in curveBindings)
        {
            AnimationCurve curve = AnimationUtility.GetEditorCurve(clip, binding);
            string propertyName = GetFriendlyPropertyName(binding);

            // Iterate through each keyframe on this curve
            foreach (Keyframe key in curve.keys)
            {
                // Each row will have the property name, the key's time, and the key's value
                sb.AppendLine($"{propertyName},{key.time.ToString("F8")},{key.value.ToString("F8")}");
            }
        }

        WriteToFile(filePath, sb.ToString(), clip.name);
    }

    // Helper function to make property names cleaner (e.g., "Animator.Chest Front-Back" -> "Chest Front-Back")
    private static string GetFriendlyPropertyName(EditorCurveBinding binding)
    {
        string name = binding.propertyName;
        // A common prefix is "m_LocalRotation.x", we can make it prettier.
        // Or "blendShape.MouthOpen"
        // Or "Animator.Chest Front-Back"
        if (name.StartsWith("m_")) name = name.Substring(2); // Remove "m_"
        name = name.Replace("Animator.", ""); // Remove "Animator."

        // Add the object path if it exists, for clarity
        if (!string.IsNullOrEmpty(binding.path))
        {
            name = $"{binding.path}/{name}";
        }
        return name;
    }

    // Helper function to write the file and show a confirmation dialog
    private static void WriteToFile(string filePath, string data, string clipName)
    {
        try
        {
            File.WriteAllText(filePath, data);
            Debug.Log($"Successfully exported animation '{clipName}' to: {filePath}");
            EditorUtility.DisplayDialog("Export Successful", $"Animation data for '{clipName}' has been exported to '{Path.GetFileName(filePath)}' in your project's root directory.", "OK");
        }
        catch (System.Exception e)
        {
            Debug.LogError("Failed to export animation: " + e.Message);
            EditorUtility.DisplayDialog("Export Failed", "Could not write the file. Check the console for errors.", "OK");
        }
    }
}