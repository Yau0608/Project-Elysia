using UnityEngine;
using System.Collections;

public class ExpressionController : MonoBehaviour
{
    public SkinnedMeshRenderer faceMesh;
    public float animationSpeed = 0.5f; // How fast to change expressions


    public AnimationCurve easingCurve;


    public void HandleExpression(string expression)
    {

        // First, reset all blendshapes to ensure a clean slate.
        ResetFace();
        // Convert to lowercase to make the matching case-insensitive and reliable
        switch (expression.ToLower().Trim())
        {
            // --- The "Happy" Bucket ---
            case "happy":
            case "smiling":
            case "grinning":
            case "joyful":
            case "pleased":
            case "content":
            case "gentlesmile":
            case "wonderstruck":
            case "playful":
                SetExpressionHappy();
                break;

            case "playfulsmile":
                SetExpressionPlayfulSmile();
                break;
            // --- The "Sad" Bucket ---
            case "sad":
            case "pouting":
            case "upset":
            case "melancholy":
                SetExpressionSad();
                break;

            case "worried":
            case "troubled":
                SetExpressionWorried();
                break;

            // --- The "Surprised" Bucket ---
            case "surprised":
            case "shocked":
            case "amazed":
                SetExpressionSurprised();
                break;


            // --- The "Angry" Bucket ---
            case "angry":
                SetExpressionAngry();
                break;

            case "neutral":
            case "reset":
                ResetFace();
                break;


            // --- THE MOST IMPORTANT PART: The Default Safety Net ---
            default:
                // If we receive an expression we don't recognize, like "wistful"...
                // ...we log it so the developer (you!) knows you might need to add a new case.
                Debug.LogWarning("Received unknown expression: '" + expression + "'. Defaulting to happy.");
                // And we play a happy animation for demonstration.
                SetExpressionHappy();
                break;
        }
    }
    // A function for each emotion

    public void SetExpressionAngry()
    {
        BlinkingController.isBlinkingEnabled = false;

        StartCoroutine(AnimateBlendshape(0, 80));
        StartCoroutine(AnimateBlendshape(17, 70));
        StartCoroutine(AnimateBlendshape(34, 90));
        StartCoroutine(AnimateBlendshape(38, 40));
    }


    public void SetExpressionGentleSmile()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(39, 60)); // 口角上げ (Mouth)
        StartCoroutine(AnimateBlendshape(21, 70)); // 慈愛 (Eye/Eyebrows)
    }

    /// <summary>
    /// A genuine, warm happiness. More expressive than GentleSmile.
    /// </summary>
    public void SetExpressionHappy()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(39, 80)); // 口角上げ (Mouth)
        StartCoroutine(AnimateBlendshape(13, 100)); // 笑い (Both Eyes)
        StartCoroutine(AnimateBlendshape(19, 40)); // 喜び (Eye/Eyebrows)
    }

    /// <summary>
    /// A thoughtful and serious expression, but still retaining her gentle nature.
    /// </summary>
    public void SetExpressionThoughtful()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(2, 30));  // 真面目 (Eyebrows)
        StartCoroutine(AnimateBlendshape(21, 40)); // 慈愛 (Eye/Eyebrows)
        StartCoroutine(AnimateBlendshape(34, 10)); // ムッ (Mouth)
    }

    // --- 2. Passionate & Direct Expressions ---

    /// <summary>
    /// A big, beaming smile for moments of true delight and excitement.
    /// </summary>
    public void SetExpressionJoyful()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(39, 95)); // 口角上げ (Mouth)
        StartCoroutine(AnimateBlendshape(57, 50)); // ^ (Mouth)
        StartCoroutine(AnimateBlendshape(13, 100)); // 笑い (Both Eyes)
    }

    /// <summary>
    /// A mix of joy and slight surprise, for reacting to exciting news.
    /// </summary>
    public void SetExpressionExcited()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(23, 25)); // びっくり (Eye/Eyebrows)
        StartCoroutine(AnimateBlendshape(19, 70)); // 喜び (Eye/Eyebrows)
        StartCoroutine(AnimateBlendshape(43, 40)); // 大口 (Mouth)
        StartCoroutine(AnimateBlendshape(39, 60)); // 口角上げ (Mouth)
    }

    // --- 3. Pure but Mischievous Expressions ---

    /// <summary>
    /// The signature mischievous smile for teasing the Trailblazer.
    /// </summary>
    public void SetExpressionPlayfulSmile()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(51, 100)); // にやり (Mouth)
        StartCoroutine(AnimateBlendshape(16, 100)); // 喜び (Eye/Eyebrows)
    }

    /// <summary>
    /// A confident, playful wink.
    /// </summary>
    public void SetExpressionWinking()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(14, 100)); // ウィンク (Right Eye)
        StartCoroutine(AnimateBlendshape(52, 60));  // にやり2 (Mouth)
        StartCoroutine(AnimateBlendshape(8, 20));   // 上 (Eyebrows)
    }

    /// <summary>
    /// A playful, "embarrassed" look used for teasing. Not genuine shyness.
    /// </summary>
    public void SetExpressionFeignedShyness()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(3, 30));  // 困る (Eyebrows)
        StartCoroutine(AnimateBlendshape(39, 40)); // 口角上げ (Mouth)
        StartCoroutine(AnimateBlendshape(50, 20)); // 口横縮げ2 (Mouth)
    }

    /// <summary>
    /// A curious expression with raised brows and a slight, interested smile.
    /// </summary>
    public void SetExpressionCurious()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(8, 50));  // 上 (Eyebrows)
        StartCoroutine(AnimateBlendshape(57, 30)); // ^ (Mouth)
        StartCoroutine(AnimateBlendshape(44, 15)); // お2 (Mouth)
    }

    // --- 4. Other Essential Emotions ---

    /// <summary>
    /// A classic, wide-eyed surprise.
    /// </summary>
    public void SetExpressionSurprised()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(23, 90)); // びっくり (Eye/Eyebrows)
        StartCoroutine(AnimateBlendshape(43, 50)); // 大口 (Mouth)
    }

    /// <summary>
    /// A genuine sad expression.
    /// </summary>
    public void SetExpressionSad()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(9, 80));  // 悲しい (Eyebrows)
        StartCoroutine(AnimateBlendshape(38, 70)); // 口角下げ (Mouth)
        StartCoroutine(AnimateBlendshape(7, 20));  // 下 (Eyebrows)
    }

    /// <summary>
    /// A worried or troubled look.
    /// </summary>
    public void SetExpressionWorried()
    {
        BlinkingController.isBlinkingEnabled = false;
        StartCoroutine(AnimateBlendshape(3, 75));  // 困る (Eyebrows)
        StartCoroutine(AnimateBlendshape(61, 60)); // 心配する (Mouth)
    }

    // You also need a way to reset the face to neutral!
    public void ResetFace()
    {
        BlinkingController.isBlinkingEnabled = true;
        // This would animate ALL the emotion sliders back to 0.
        // Reset all relevant blendshapes to 0
        StartCoroutine(AnimateBlendshape(0, 0));
        StartCoroutine(AnimateBlendshape(1, 0));
        StartCoroutine(AnimateBlendshape(2, 0));
        StartCoroutine(AnimateBlendshape(3, 0));
        StartCoroutine(AnimateBlendshape(4, 0));
        StartCoroutine(AnimateBlendshape(5, 0));
        StartCoroutine(AnimateBlendshape(6, 0));
        StartCoroutine(AnimateBlendshape(7, 0));
        StartCoroutine(AnimateBlendshape(8, 0));
        StartCoroutine(AnimateBlendshape(9, 0));
        StartCoroutine(AnimateBlendshape(10, 0));
        StartCoroutine(AnimateBlendshape(11, 0));
        StartCoroutine(AnimateBlendshape(12, 0));
        StartCoroutine(AnimateBlendshape(13, 0));
        StartCoroutine(AnimateBlendshape(14, 0));
        StartCoroutine(AnimateBlendshape(15, 0));
        StartCoroutine(AnimateBlendshape(16, 0));
        StartCoroutine(AnimateBlendshape(17, 0));
        StartCoroutine(AnimateBlendshape(18, 0));
        StartCoroutine(AnimateBlendshape(19, 0));
        StartCoroutine(AnimateBlendshape(20, 0));
        StartCoroutine(AnimateBlendshape(21, 0));
        StartCoroutine(AnimateBlendshape(22, 0));
        StartCoroutine(AnimateBlendshape(23, 0));
        StartCoroutine(AnimateBlendshape(24, 0));
        StartCoroutine(AnimateBlendshape(25, 0));
        StartCoroutine(AnimateBlendshape(26, 0));
        StartCoroutine(AnimateBlendshape(27, 0));
        StartCoroutine(AnimateBlendshape(28, 0));
        StartCoroutine(AnimateBlendshape(29, 0));
        StartCoroutine(AnimateBlendshape(30, 0));
        StartCoroutine(AnimateBlendshape(31, 0));
        StartCoroutine(AnimateBlendshape(32, 0));
        StartCoroutine(AnimateBlendshape(33, 0));
        StartCoroutine(AnimateBlendshape(34, 0));
        StartCoroutine(AnimateBlendshape(35, 0));
        StartCoroutine(AnimateBlendshape(36, 0));
        StartCoroutine(AnimateBlendshape(37, 0));
        StartCoroutine(AnimateBlendshape(38, 0));
        StartCoroutine(AnimateBlendshape(39, 0));
        StartCoroutine(AnimateBlendshape(40, 0));
        StartCoroutine(AnimateBlendshape(41, 0));
        StartCoroutine(AnimateBlendshape(42, 0));
        StartCoroutine(AnimateBlendshape(43, 0));
        StartCoroutine(AnimateBlendshape(44, 0));
        StartCoroutine(AnimateBlendshape(45, 0));
        StartCoroutine(AnimateBlendshape(46, 0));
        StartCoroutine(AnimateBlendshape(47, 0));
        StartCoroutine(AnimateBlendshape(48, 0));
        StartCoroutine(AnimateBlendshape(49, 0));
        StartCoroutine(AnimateBlendshape(50, 0));
        StartCoroutine(AnimateBlendshape(51, 0));
        StartCoroutine(AnimateBlendshape(52, 0));
        StartCoroutine(AnimateBlendshape(53, 0));
        StartCoroutine(AnimateBlendshape(54, 0));
        StartCoroutine(AnimateBlendshape(55, 0));
        StartCoroutine(AnimateBlendshape(56, 0));
        StartCoroutine(AnimateBlendshape(57, 0));
        StartCoroutine(AnimateBlendshape(58, 0));
        StartCoroutine(AnimateBlendshape(59, 0));
        StartCoroutine(AnimateBlendshape(60, 0));
        StartCoroutine(AnimateBlendshape(61, 0));
        StartCoroutine(AnimateBlendshape(62, 0));
        StartCoroutine(AnimateBlendshape(63, 0));
        StartCoroutine(AnimateBlendshape(64, 0));
        StartCoroutine(AnimateBlendshape(65, 0));
        StartCoroutine(AnimateBlendshape(66, 0));
        StartCoroutine(AnimateBlendshape(67, 0));
        StartCoroutine(AnimateBlendshape(68, 0));
        StartCoroutine(AnimateBlendshape(69, 0));
        StartCoroutine(AnimateBlendshape(70, 0));
        StartCoroutine(AnimateBlendshape(71, 0));
        StartCoroutine(AnimateBlendshape(72, 0));
        StartCoroutine(AnimateBlendshape(73, 0));
        StartCoroutine(AnimateBlendshape(74, 0));
        StartCoroutine(AnimateBlendshape(75, 0));
        StartCoroutine(AnimateBlendshape(76, 0));
        StartCoroutine(AnimateBlendshape(77, 0));
        StartCoroutine(AnimateBlendshape(78, 0));
        StartCoroutine(AnimateBlendshape(79, 0));
        StartCoroutine(AnimateBlendshape(80, 0));
    }

    void Update()
    {
        /*
        if (Input.GetKeyDown(KeyCode.H))
        {
            SetExpressionHappy();
        }

        if (Input.GetKeyDown(KeyCode.S))
        {
            SetExpressionSad();
        }

        if (Input.GetKeyDown(KeyCode.A))
        {
            SetExpressionAngry();
        }

        if (Input.GetKeyDown(KeyCode.P))
        {
            SetExpressionSurprised();
        }

        if (Input.GetKeyDown(KeyCode.R))
        {
            ResetFace();
        }
        */
    }

    // This is the generic animation function, based on your blink script.
    IEnumerator AnimateBlendshape(int index, float targetWeight)
    {
        float startWeight = faceMesh.GetBlendShapeWeight(index);
        float elapsedTime = 0f;

        while (elapsedTime < animationSpeed)
        {
            float progress = elapsedTime / animationSpeed;

            float t = easingCurve.Evaluate(progress); // Use the easing curve for smooth transitions

            float currentWeight = Mathf.Lerp(startWeight, targetWeight, t);
            faceMesh.SetBlendShapeWeight(index, currentWeight);
            elapsedTime += Time.deltaTime;
            yield return null;
        }

        faceMesh.SetBlendShapeWeight(index, targetWeight); // Ensure it reaches the target
    }

}