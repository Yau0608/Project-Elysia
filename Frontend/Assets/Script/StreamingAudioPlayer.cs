using System;
using System.Collections.Generic;
using UnityEngine;

[RequireComponent(typeof(AudioSource))]
public class StreamingAudioPlayer : MonoBehaviour
{
    private readonly Queue<float> audioBuffer = new Queue<float>();
    private readonly object audioBufferLock = new object();
    private bool isReceiving = false;
    private AudioSource audioSource;
    private int sourceSampleRate = 32000;
    private int outputSampleRate = 48000;
    private float stopAfterBufferDrainAt = -1f;
    private float drainDelaySeconds = 0.15f;

    // This allows other scripts (like ConnectionManager) to know when the audio actually finishes
    public Action OnStreamComplete;

    void Awake()
    {
        audioSource = GetComponent<AudioSource>();
        outputSampleRate = AudioSettings.outputSampleRate;
        audioSource.loop = true;
        ConfigureStreamingClip(outputSampleRate);
    }

    void ConfigureStreamingClip(int sampleRate)
    {
        if (audioSource.isPlaying)
        {
            audioSource.Stop();
        }

        audioSource.clip = AudioClip.Create(
            "StreamDummy",
            Math.Max(sampleRate, 1024),
            1,
            sampleRate,
            true,
            OnAudioRead
        );
    }

    public void StartReceiving(int sampleRate)
    {
        lock (audioBufferLock)
        {
            audioBuffer.Clear();
        }

        sourceSampleRate = sampleRate > 0 ? sampleRate : outputSampleRate;
        AudioSettings.GetDSPBufferSize(out int bufferLength, out int numBuffers);
        drainDelaySeconds = Mathf.Max(0.1f, (bufferLength * numBuffers) / (float)sourceSampleRate + 0.05f);
        stopAfterBufferDrainAt = -1f;
        ConfigureStreamingClip(sourceSampleRate);
        isReceiving = true;
        Debug.Log($"[STREAM] Source sample rate: {sourceSampleRate}, output sample rate: {outputSampleRate}");
        audioSource.Play();
    }

    public void AddChunkBase64(string base64)
    {
        // 1. Decode Base64 string to raw bytes
        byte[] pcmBytes = Convert.FromBase64String(base64);

        // 2. Convert 16-bit PCM bytes to floats (-1.0 to 1.0) for Unity
        lock (audioBufferLock)
        {
            for (int i = 0; i < pcmBytes.Length; i += 2)
            {
                short sample16 = BitConverter.ToInt16(pcmBytes, i);
                audioBuffer.Enqueue(sample16 / 32768f);
            }
        }
    }

    public void StopReceiving()
    {
        isReceiving = false;
    }

    void OnAudioRead(float[] data)
    {
        lock (audioBufferLock)
        {
            for (int i = 0; i < data.Length; i++)
            {
                if (audioBuffer.Count > 0)
                {
                    data[i] = audioBuffer.Dequeue();
                }
                else
                {
                    data[i] = 0f;
                }
            }
        }
    }

    void Update()
    {
        // If Python finished sending, AND we finished playing the last chunk in the buffer...
        int bufferedSampleCount;
        lock (audioBufferLock)
        {
            bufferedSampleCount = audioBuffer.Count;
        }

        if (!isReceiving && bufferedSampleCount <= 0 && audioSource.isPlaying)
        {
            if (stopAfterBufferDrainAt < 0f)
            {
                stopAfterBufferDrainAt = Time.unscaledTime + drainDelaySeconds;
            }
            else if (Time.unscaledTime >= stopAfterBufferDrainAt)
            {
                audioSource.Stop();
                stopAfterBufferDrainAt = -1f;
                OnStreamComplete?.Invoke(); // Fire the event to reset her face!
            }
        }
        else
        {
            stopAfterBufferDrainAt = -1f;
        }
    }
}
