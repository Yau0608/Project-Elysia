using UnityEngine;
using System;

namespace Dollars
{
    public class GestureListener : MonoBehaviour
    {
        public static event Action<string> OnHandGestureDetected;
        public static event Action<string, float> OnGestureDetected;

        public void ReceiveHandGesture(string gesture)
        {
            OnHandGestureDetected?.Invoke(gesture);
        }

        public void ReceiveGesture(string gesture, float value)
        {
            OnGestureDetected?.Invoke(gesture, value);
        }
    }
}
