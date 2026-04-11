using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BlinkingController : MonoBehaviour
{
    public SkinnedMeshRenderer faceMesh;
    public float animationDuration = 0.08f; // Blinks are fast!

    // --- Control variables we can tweak in the Inspector ---
    [Header("Blink Timing")]
    public float minBlinkInterval = 2.0f; // Minimum time between blinks
    public float maxBlinkInterval = 7.0f; // Maximum time between blinks
    public float doubleBlinkChance = 0.2f; // 20% chance for a double blink
    // It's 'static' so any script can access it easily without a direct reference.

    // --- This is our "Master Control Switch" for other scripts ---
    ///  It's 'static' so any script can access it easily without a direct reference.
    public static bool isBlinkingEnabled = true;

    // When the game starts, we begin our main blinking routine.
    void Start()
    {
        StartCoroutine(BlinkRoutine());
    }

    // The main routine that decided WHEN to blink.
    IEnumerator BlinkRoutine()
    {
        // This 'while (true)' loop will run forever for the entire game.
        while (true)
        {
            // 1. Wait for a random amount of time.
            float delay = Random.Range(minBlinkInterval, maxBlinkInterval);
            yield return new WaitForSeconds(delay);

            // 2. Check if blinking is allowed by the "Master Control Switch".
            if (isBlinkingEnabled)
            {
                // 3. Decide if we should do a single or double blink.
                if (Random.value < doubleBlinkChance)
                {
                    StartCoroutine(SmoothDoubleBlink());
                }
                else
                {
                    StartCoroutine(SmoothSingleBlink());
                }
            }
        }
    }

    // This is your excellent smooth blink logic, now for a single blink.
    IEnumerator SmoothSingleBlink()
    {
        // Close eyes
        float elapsedTime = 0f;
        while (elapsedTime < animationDuration)
        {
            faceMesh.SetBlendShapeWeight(10, Mathf.Lerp(0, 100, elapsedTime / animationDuration));
            elapsedTime += Time.deltaTime;
            yield return null;
        }
        faceMesh.SetBlendShapeWeight(10, 100);

        // Open eyes
        elapsedTime = 0f;
        while (elapsedTime < animationDuration)
        {
            faceMesh.SetBlendShapeWeight(10, Mathf.Lerp(100, 0, elapsedTime / animationDuration));
            elapsedTime += Time.deltaTime;
            yield return null;
        }
        faceMesh.SetBlendShapeWeight(10, 0);
    
    }

    IEnumerator SmoothDoubleBlink()
    {
        yield return StartCoroutine(SmoothSingleBlink()); // Perform the first blink
        yield return new WaitForSeconds(0.1f); // A tiny pause
        yield return StartCoroutine(SmoothSingleBlink()); // Perform the second blink
    }
    void Update()
    {
        
    }
}
