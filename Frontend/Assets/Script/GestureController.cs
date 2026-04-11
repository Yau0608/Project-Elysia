using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GestureController : MonoBehaviour
{

    // We need a reference to the Animator, which controls the body.
    private Animator characterAnimator;

    [Header("Testing")]
    public string defaultTestGesture = "thinking";



    private void Start()
    {
        characterAnimator = GetComponent<Animator>();

        if (characterAnimator == null)
        {
            Debug.LogError("GestureController: Animator component not found! Cannot play gestures.");
        }
    }
    public void PlayGesture(string gestureName)
    {
        if (characterAnimator == null) return;
        if (string.IsNullOrEmpty(gestureName)) return;

        // Convert to lowercase for reliable matching
        string gesture = gestureName.ToLower().Trim();
        if (gesture == "idle" || gesture == "none")
        {
            // Do nothing for idle gestures.
            return;
        }

        // 'Contain matching' logic
        if (gesture.Contains("nod")) // Catches "Nod", "SlightNod", "HeadNod"
        {
            Debug.Log($"Interpreted '{gestureName}' as Nod.");
            characterAnimator.SetTrigger("nod");
        }
        else if (gesture.Contains("wave")) // Catches "Wave", "FriendlyWave"
        {
            Debug.Log($"Interpreted '{gestureName}' as Wave.");
            characterAnimator.SetTrigger("waving");
        }
        else if (gesture.Contains("think")) // Catches "Think", "Thinking"
        {
            Debug.Log($"Interpreted '{gestureName}' as Thinking.");
            characterAnimator.SetTrigger("thinking");
        }
        else if (gesture.Contains("tilt")) // Catches "Think", "Thinking"
        {
            Debug.Log($"Interpreted '{gestureName}' as Thinking.");
            characterAnimator.SetTrigger("thinking");
        }
        else 
        {
            // Out default safety net
            Debug.LogWarning($"Received unknow gesture: '{gestureName}'. Playing no gesture.");
        }
    }




}


