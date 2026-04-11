using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using uOSC;
using EVMC4U;

namespace Dollars
{
    public class MoCapManager : MonoBehaviour
    {
        public int ListenOnPort = 39539;
        uOscServer os;
        ExternalReceiver re;
        [SerializeField]
        [Range(0.0f, 0.99f)]
        private float _smoothness = 0.3f;
        public float Smoothness
        {
            get { return _smoothness; }
            set
            {
                _smoothness = value;
                if (re != null)
                {
                    re.BoneFilter = value;
                }
            }
        }
        void OnValidate()
        {
            if (re != null)
            {
                re.BoneFilter = Smoothness;
            }
        }
        // Start is called before the first frame update
        void Start()
        {
            os = gameObject.AddComponent<uOscServer>();
            os.enabled = false;
            os.port = ListenOnPort;
            os.enabled = true;
            re = gameObject.AddComponent<ExternalReceiver>();
            re.BoneFilter = Smoothness;
        }

        // Update is called once per frame
        void Update()
        {

        }
    }
}
