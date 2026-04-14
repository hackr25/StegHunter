import cv2
import numpy as np
from PIL import Image

class CloneDetector:
    """
    Detects Copy-Move Forgery by finding identical patches 
    of pixels within the same image using ORB descriptors.
    """
    def __init__(self, similarity_threshold=0.8, min_match_dist=20):
        self.similarity_threshold = similarity_threshold
        self.min_match_dist = min_match_dist

    def analyze(self, image_path) -> dict:
        try:
            # Load image in grayscale
            img = cv2.imread(image_path)
            if img is None:
                return {"error": "Could not read image", "suspicion_score": 0.0}
            
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 1. Initialize ORB detector
            orb = cv2.ORB_create(nfeatures=1000)
            
            # 2. Find keypoints and descriptors
            kp, des = orb.detectAndCompute(gray, None)
            
            if des is None or len(des) < 10:
                return {"matches": 0, "suspicion_score": 0.0, "method": "Clone Detection"}

            # 3. Match descriptors against themselves (Brute Force)
            # We use BFMatcher with Hamming distance (best for ORB)
            bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
            matches = bf.match(des, des)

            # 4. Filter matches
            # We ignore matches that are:
            # - The same point (distance == 0)
            # - Too close to each other (natural texture)
            valid_clones = 0
            for m in matches:
                # Distance is the difference between descriptors
                if 0 < m.distance < 30: # Low distance = high similarity
                    # Check if the keypoints are far enough apart to be a 'copy'
                    p1 = kp[m.queryIdx].pt
                    p2 = kp[m.trainIdx].pt
                    dist = np.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)
                    
                    if dist > self.min_match_dist:
                        valid_clones += 1

            # 5. Calculate suspicion score
            # A high number of identical patches is extremely rare in natural images.
            # We scale based on the number of matches found.
            suspicion_score = 0.0
            if valid_clones > 10:
                suspicion_score = min(100.0, valid_clones * 2.0)

            return {
                "clone_matches": valid_clones,
                "suspicion_score": round(suspicion_score, 2),
                "method": "Clone Detection"
            }
        except Exception as e:
            return {"error": str(e), "suspicion_score": 0.0}
