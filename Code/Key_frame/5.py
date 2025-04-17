import cv2
import numpy as np
import os
from math import log
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image
import urllib.request

def compute_mutual_information(img1, img2, histSize=50):
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)
    channel = 0
    h1 = hsv1[:, :, channel]
    h2 = hsv2[:, :, channel]
    hist1 = cv2.calcHist([h1], [0], None, [histSize], [0, 180])
    hist2 = cv2.calcHist([h2], [0], None, [histSize], [0, 180])
    hist1 = hist1 / np.sum(hist1)
    hist2 = hist2 / np.sum(hist2)
    def entropy(hist):
        hist_nonzero = hist[hist > 0]
        return -np.sum(hist_nonzero * np.log(hist_nonzero))
    H1 = entropy(hist1)
    H2 = entropy(hist2)
    joint_hist = cv2.calcHist([h1, h2], [0, 0], None, [histSize, histSize], [0, 180, 0, 180])
    joint_hist = joint_hist / np.sum(joint_hist)
    def joint_entropy(jhist):
        jhist_nonzero = jhist[jhist > 0]
        return -np.sum(jhist_nonzero * np.log(jhist_nonzero))
    H_joint = joint_entropy(joint_hist)
    mi = H1 + H2 - H_joint
    return mi

def extract_candidate_patch(img, patch_size=224):
    try:
        sift = cv2.SIFT_create()
    except Exception as e:
        print("Utilisation de cv2.xfeatures2d.SIFT_create() :", e)
        sift = cv2.xfeatures2d.SIFT_create()
    keypoints, descriptors = sift.detectAndCompute(img, None)
    if not keypoints:
        return None
    best_kp = max(keypoints, key=lambda kp: kp.response)
    x, y = best_kp.pt
    x, y = int(x), int(y)
    h, w = img.shape[:2]
    half = patch_size // 2
    left = max(x - half, 0)
    top = max(y - half, 0)
    if left + patch_size > w or top + patch_size > h:
        return None
    patch = img[top:top+patch_size, left:left+patch_size]
    return patch

def load_imagenet_labels():
    url = "https://raw.githubusercontent.com/pytorch/hub/master/imagenet_classes.txt"
    try:
        response = urllib.request.urlopen(url)
        labels = [line.decode('utf-8').strip() for line in response.readlines()]
    except Exception as e:
        print("Erreur lors du chargement des labels ImageNet:", e)
        labels = []
    return labels

def classify_patch(model, patch, device, transform, labels, target_keywords=['train', 'locomotive']):
    patch_rgb = cv2.cvtColor(patch, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(patch_rgb)
    input_tensor = transform(pil_img).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(input_tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        top_prob, top_idx = torch.max(probabilities, 1)
        top_idx = top_idx.item()
        top_prob = top_prob.item()
        predicted_label = labels[top_idx] if labels else str(top_idx)
    if any(keyword in predicted_label.lower() for keyword in target_keywords) and top_prob > 0.2:
        return True, predicted_label, top_prob
    else:
        return False, predicted_label, top_prob

def extract_key_frames(video_path, sampling_interval=10, mi_threshold=0.5, output_dir='keyframes_5'):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Utilisation de torchvision pour charger AlexNet pré-entraîné sur ImageNet
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = models.alexnet(pretrained=True)
    model.to(device)
    model.eval()
    
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                             std=[0.229, 0.224, 0.225])
    ])
    labels = load_imagenet_labels()
    
    cap = cv2.VideoCapture(video_path)
    prev_frame = None
    frame_idx = 0
    key_frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % sampling_interval == 0:
            if prev_frame is None:
                candidate = frame.copy()
                key_frames.append((frame_idx, candidate))
                prev_frame = candidate
            else:
                mi = compute_mutual_information(prev_frame, frame)
                print(f"Frame {frame_idx} -- MI = {mi:.3f}")
                if mi < mi_threshold:
                    patch = extract_candidate_patch(frame)
                    if patch is not None:
                        valid, pred_label, prob = classify_patch(model, patch, device, transform, labels)
                        print(f"Frame {frame_idx} : Label = {pred_label}, probabilité = {prob:.3f}")
                        if valid:
                            candidate = frame.copy()
                            key_frames.append((frame_idx, candidate))
                            prev_frame = candidate
        frame_idx += 1
    cap.release()
    for idx, (f_idx, img) in enumerate(key_frames):
        filename = os.path.join(output_dir, f"keyframe_{f_idx:04d}.jpg")
        cv2.imwrite(filename, img)
        print(f"Key frame sauvegardée : {filename}")
    print(f"Nombre total de key frames détectées : {len(key_frames)}")
    return key_frames

if __name__ == '__main__':
    video_file = '../../Film/BDD_video_varié/drone.mp4' 
    #video_file = '../../Film/BDD_video_varié/rugby.mp4'
    #video_file = '../../Film/BDD_video_varié/vs_fixe.mp4' 

    extract_key_frames(video_file, sampling_interval=1, mi_threshold=0.5)

