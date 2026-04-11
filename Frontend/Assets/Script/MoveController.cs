using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MoveController : MonoBehaviour
{
    private Animator characterAnimator;
    // Start is called before the first frame update

    private void Awake()
    {
        characterAnimator = GetComponent<Animator>();
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.W))
        {
            print("Now Waving");
            characterAnimator.SetTrigger("DoWave");
        }
        if (Input.GetKeyDown(KeyCode.S))
        {
            print("Now Sitting");
            characterAnimator.SetBool("sitting", true);
        }
        if (Input.GetKeyDown(KeyCode.I))
        {
            print("Back To Idle");
            characterAnimator.SetBool("sitting", false);
        }
    }
}
