import cv2

def get_feature_detector(model_name):
    if model_name == "sift":
        return cv2.SIFT_create()
    elif model_name == "orb":
        return cv2.ORB_create(nfeatures=2000)
    elif model_name == "orb-cuda":
        return cv2.cuda_ORB.create(nfeatures=2000)
    else:
        raise ValueError(f"Unknown model: {model_name}")

def extract_features(img, model_name):
    if model_name == "orb-cuda":
        if not cv2.cuda.getCudaEnabledDeviceCount():
            raise RuntimeError("CUDA device not found for orb-cuda")

        gpu_img = cv2.cuda_GpuMat()
        gpu_img.upload(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
        detector = get_feature_detector(model_name)
        kp, desc = detector.detectAndComputeAsync(gpu_img, None)
        kp = detector.convert(kp)
        desc = desc.download()
    else:
        detector = get_feature_detector(model_name)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        kp, desc = detector.detectAndCompute(gray, None)

    return kp, desc
