using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class StreamingAudioPlayer : MonoBehaviour
{
    private Queue<float> audioBuffer = new Queue<float>();
    private bool isReceiving = false;
    private AudioSource audioSource;

    // This allows other scripts (like ConnectionManager) to know when the audio actually finishes
    public Action OnStreamComplete;

    void Awake()
    {
        audioSource = GetComponent<AudioSource>();
        // Create a dummy clip to keep the AudioSource active so OnAudioFilterRead runs
        audioSource.clip = AudioClip.Create("StreamDummy", 32000, 1, 32000, false);
        audioSource.loop = true;
    }

    public void StartReceiving()
    {
        audioBuffer.Clear();
        isReceiving = true;
        audioSource.Play();
    }

    public void AddChunkBase64(string base64)
    {
        // 1. Decode Base64 string to raw bytes
        byte[] pcmBytes = Convert.FromBase64String(base64);

        // 2. Convert 16-bit PCM bytes to floats (-1.0 to 1.0) for Unity
        for (int i = 0; i < pcmBytes.Length; i += 2)
        {
            short sample16 = BitConverter.ToInt16(pcmBytes, i);
            audioBuffer.Enqueue(sample16 / 32768f);
        }
    }

    public void StopReceiving()
    {
        isReceiving = false;
    }

    // This is a special Unity function that injects our raw numbers directly into the speaker
    void OnAudioFilterRead(float[] data, int channels)
    {
        for (int i = 0; i < data.Length; i += channels)
        {
            float sample = 0f;
            // If we have downloaded chunks, play them
            if (audioBuffer.Count > 0)
            {
                sample = audioBuffer.Dequeue();
            }

            // Output the sound to all speakers (left/right)
            for (int c = 0; c < channels; c++)
            {
                data[i + c] = sample;
            }
        }
    }

    void Update()
    {
        // If Python finished sending, AND we finished playing the last chunk in the buffer...
        if (!isReceiving && audioBuffer.Count == 0 && audioSource.isPlaying)
        {
            audioSource.Stop();
            OnStreamComplete?.Invoke(); // Fire the event to reset her face!
        }
    }
}