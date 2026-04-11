using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class BlinkTest : MonoBehaviour
{
    public SkinnedMeshRenderer faceMesh;

    // We can control the speed of the animation from the Unity editor now!
    public float animationDuration = 0.15f; // How long it takes to close or open the eyes

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.B))
        {
            // We call the coroutine the same way.
            StartCoroutine(SmoothBlink());
        }
    }


    // This is our new, smooth blinking function.
    IEnumerator SmoothBlink()
    {
        // === PART 1: CLOSING THE EYES ===

        float elapsedTime = 0f; // This is our timer.

        // A 'while' loop that runs as long as our timer is less than the animation duration.
        while (elapsedTime < animationDuration)
        {
            // Calculate our progress (a value from 0.0 to 1.0)
            float t = elapsedTime / animationDuration;

            // Use Lerp to find the current weight between 0 and 100 based on our progress.
            float currentWeight = Mathf.Lerp(0, 100, t);

            // Set the blendshape to this new, calculated weight.
            faceMesh.SetBlendShapeWeight(10, currentWeight);

            // Increase our timer by the amount of time that has passed since the last frame.
            elapsedTime += Time.deltaTime;

            // THIS IS IMPORTANT: 'yield return null' tells the loop to pause here and wait for the next frame.
            // This is how we animate over multiple frames instead of freezing the game.
            yield return null;
        }

        // Just to be sure, we set the final weight to 100 to make sure it's fully closed.
        faceMesh.SetBlendShapeWeight(10, 100);


        // === PART 2: OPENING THE EYES (the reverse process) ===

        elapsedTime = 0f; // Reset our timer.

        while (elapsedTime < animationDuration)
        {
            float t = elapsedTime / animationDuration;

            // This time, we Lerp from 100 (closed) back down to 0 (open).
            float currentWeight = Mathf.Lerp(100, 0, t);

            faceMesh.SetBlendShapeWeight(10, currentWeight);
            elapsedTime += Time.deltaTime;
            yield return null; // Wait for the next frame
        }

        // And finally, set the weight back to 0 to ensure it's fully open.
        faceMesh.SetBlendShapeWeight(10, 0);
    }
}