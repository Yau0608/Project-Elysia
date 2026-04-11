using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class SmileTest : MonoBehaviour
{
    // Start is called before the first frame update
    public SkinnedMeshRenderer facemesh;

    public float smileSpeed = 0.1f;
    // Update is called once per frame
    void Update()
    {

        if (Input.GetKeyDown(KeyCode.S))
        {
            StartCoroutine(Smile());
        }
    }


    IEnumerator Smile()
    {
        facemesh.SetBlendShapeWeight(14, 100); // Assuming blend shape index 0 is for blinking

        yield return new WaitForSeconds(smileSpeed);

        facemesh.SetBlendShapeWeight(14, 0);
    }
}
