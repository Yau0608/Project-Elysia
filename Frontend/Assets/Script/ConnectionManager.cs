// In ConnectionManager.cs

using JetBrains.Annotations;
using NativeWebSocket;
using System;
using System.Collections;
using System.Collections.Generic;
using System.Net;
using TMPro;
using uLipSync;
using UnityEngine;

[System.Serializable]
public class ElysiaResponseForLogging
{
    // This class is identical to ElysiaResponse, but without the audio_base64 field.
    public string dialogue;
    public string expression;
    public string gesture;
    public string internal_thought_in_character;
}

// --- Step 1: Define the NEW JSON structure ---
// This class MUST perfectly match the JSON keys from your Python server.
[System.Serializable]
public class UnityMessage
{ 
    public string @event; // The event type, e.g., "audio_data"
    public string data; // The actual data, e.g., base64 audio string
}
public class ElysiaResponse
{
    public string dialogue;
    public string expression;
    public string gesture;
    public string internal_thought_in_character;
    public string audio_base64;
}

public class ConnectionManager : MonoBehaviour
{
    WebSocket websocket;

    // --- Step 2: Add references for our new components ---
    public Animator characterAnimator; // This is the Animator component for the character
    public ExpressionController expressionController; // This is the component that controls facial expressions
    public GestureController gestureController; // This is the component that controls gestures (if you have one)
    public GameObject dialoguePanel; // This is the parent panel for dialogue
    public TextMeshProUGUI dialogueTextUI; // This is the text UI for dialogue
    public GameObject internalThoughtPanel; // Link to the parent panel
    public TextMeshProUGUI internalThoughtTextUI; // This is the text UI for internal thoughts
    public AudioSource characterAudioSource; // A link to the AudioSource component
    public UnityEngine.UI.Image micButtonImage;

    private readonly Queue<Action> mainThreadActions = new Queue<Action>();

    private bool isRecording = false;
    private AudioClip recordingClip;
    private string microphoneDevice;

    public void OnStartRecordingButtonPressed()
    { 
        StartRecording();
    }

    public void OnStopRecordingButtonPressed()
    {
        StopRecordingAndSend();
    }

    public void ToggleInternalThought()
    {
        // This line is a clever way to toggle a GameObject on and off.
        // It sets the panel to be the opposite of whatever its current state is.
        internalThoughtPanel.SetActive(!internalThoughtPanel.activeSelf);
    }
    void Start()
    {
        // It's good practice to check if all components are linked in the Inspector.
        if (characterAnimator == null || expressionController == null || dialogueTextUI == null || internalThoughtTextUI == null || characterAudioSource == null || gestureController == null)
        {
            Debug.LogError("[CRITICAL ERROR] One or more component links are missing on the ConnectionManager in the Inspector!Please link all of them.");
            return;
        }
        Debug.Log("All components successfully linked in the Inspector!");
        ConnectToServer();
        if (Microphone.devices.Length > 0)
        {
            microphoneDevice = Microphone.devices[0];
            Debug.Log("Found microphone: " + microphoneDevice);
        }
        else
        {
            Debug.LogError("No microphone found!");
        }
    }

    public void StartRecording()
    {
        if (isRecording) return;

        Debug.Log("Starting recording...");
        isRecording = true;

        if (micButtonImage != null)
        {
            micButtonImage.color = Color.red;
        }

        recordingClip = Microphone.Start(microphoneDevice, false, 15, 44100);
    
    }

    public async void StopRecordingAndSend()
    { 
        if (!isRecording) return; ;

        Debug.Log("Stopping recording and sending data...");

        if (micButtonImage != null)
        {
            micButtonImage.color = Color.white;
        }

        int lastSample = Microphone.GetPosition(microphoneDevice);
        Microphone.End(microphoneDevice);
        isRecording = false;
        // Get the raw audio data as a float array
        float[] samples = new float[lastSample];
        recordingClip.GetData(samples, 0);

        // --- NEW: Convert float[] to byte[] manually ---
        byte[] audioBytes = new byte[samples.Length * 2];
        int byteIndex = 0;
        for (int i = 0; i < samples.Length; i++)
        {

            short intSample = (short)(samples[i] * 32767);
            byte[] intBytes = BitConverter.GetBytes(intSample);
            audioBytes[byteIndex++] = intBytes[0];
            audioBytes[byteIndex++] = intBytes[1];
        
        }
        string audioBase64 = Convert.ToBase64String(audioBytes);

        UnityMessage messageData = new UnityMessage();
        messageData.@event = "audio_data";
        messageData.data = audioBase64;
        string jsonMessage = JsonUtility.ToJson(messageData);

        Debug.Log("Sending JSON: " + jsonMessage);

        if (websocket != null && websocket.State == WebSocketState.Open)
        {
            await websocket.SendText(jsonMessage);
            Debug.Log("Sent audio data to server.");
        }
    }

    async void ConnectToServer()
    {
        
        websocket = new WebSocket("ws://localhost:8765");

        websocket.OnOpen += () => { Debug.Log("[1] Connection open!"); };
        websocket.OnError += (e) => { Debug.Log("[ERROR] " + e); };
        websocket.OnClose += (e) => { Debug.Log("[X] Connection closed!"); };
        websocket.OnMessage += (bytes) =>
        {
            // First, decode the raw bytes into a JSON string.
            var jsonString = System.Text.Encoding.UTF8.GetString(bytes);
            Debug.Log("Received JSON: " + jsonString);
            // New elysia log that don't have the huge audio_base64 field, for logging purposes.
            ElysiaResponseForLogging logResponse = JsonUtility.FromJson<ElysiaResponseForLogging>(jsonString);
            string sanitizedJson = JsonUtility.ToJson(logResponse, true); // 'true' makes it pretty-print
            Debug.Log("Received Sanitized JSON: \n" + sanitizedJson);

            // Original Elysia response with audio data, for playing the character's turn.
            ElysiaResponse response = JsonUtility.FromJson<ElysiaResponse>(jsonString);

            mainThreadActions.Enqueue(() => {
                // We just start the master coroutine and pass it the data it needs.
                StartCoroutine(PlayCharacterTurn(response));
            });
        };

        await websocket.Connect();
    }

    IEnumerator PlayCharacterTurn(ElysiaResponse response)
    {
        // === Step A: Preparation ===

        // First, let's get the audio ready so we know how long it is.
        if (string.IsNullOrEmpty(response.audio_base64))
        {
            Debug.LogError("Cannot play turn, audio data is empty.");
            yield break;
        }
        byte[] audioBytes = System.Convert.FromBase64String(response.audio_base64);
        AudioClip clip = WavUtility.ToAudioClip(audioBytes);
        float audioDuration = clip.length; // Get the duration of the audio in seconds.
    
        // --- The Performance Begins ---

        // === Step B: Set the Expression and Dialogue ===

        // Make the panels visible!
        dialoguePanel.SetActive(true);
        internalThoughtPanel.SetActive(false);

        expressionController.HandleExpression(response.expression);
        gestureController.PlayGesture(response.gesture);

        dialogueTextUI.text = response.dialogue;
        internalThoughtTextUI.text = response.internal_thought_in_character;
        

        // === Step C: Play the Audio ===

        // Play the audio clip.
        characterAudioSource.PlayOneShot(clip);

        // === Step D: Wait for the Audio to Finish ===

        // This is the magic. The coroutine will pause here for the exact
        // duration of the audio clip, plus a tiny buffer.
        yield return new WaitForSeconds(audioDuration + 0.5f);

        // === Step E: Reset the State ===

        // Once the dialogue is finished, reset the expression back to neutral.
        expressionController.HandleExpression("neutral");
        // dialoguePanel.SetActive(false);
    }


    public void OnTalkButtonPressed()
    {
        if (isRecording)
        {
            StopRecordingAndSend();
        }
        else
        {
            StartRecording();
        }
    
    }

    void Update()
    {
        if (websocket != null)
        {
            websocket.DispatchMessageQueue();
        }

        while (mainThreadActions.Count > 0)
        {
            Action action = mainThreadActions.Dequeue();
            action();
        }
    }

    private async void OnApplicationQuit()
    {
        if (websocket != null) { await websocket.Close(); }
    }
}