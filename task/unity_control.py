class UnityControl:
    """
    Simulates control of a Unity 3D character model.
    For now, it just prints what it would do.
    """

    def __init__(self):
        print("UnityControl initialized (mock mode).")

    def set_expression(self, emotion_data_received):
        """
        Simulates setting the character's facial expression in Unity.

        Args:
            emotion_name (str): The name of the emotion (e.g., "happy", "sad", "angry").
        
        Returns:
            str:A status message.
        """
        print(f"UNITY MOCK: Setting character expression to:{emotion_data_received.upper()}!")
        return f"Character expression set to {emotion_data_received.upper()}"
        
        
    # Can add more methods here later for other actions
    # def move_forward(self, distance):
    #     print(f"UNITY MOCK: Moving forward by {distance} units.")
    #     return f"Character moved forward by {distance}."