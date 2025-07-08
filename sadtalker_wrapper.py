# sadtalker_wrapper.py

import os
import shutil
import torch
from time import strftime
from src.utils.preprocess import CropAndExtract
from src.test_audio2coeff import Audio2Coeff
from src.facerender.animate import AnimateFromCoeff
from src.generate_batch import get_data
from src.generate_facerender_batch import get_facerender_data
from src.utils.init_path import init_path

def generate_talking_video(source_image, driven_audio, checkpoint_dir, result_dir, device='cpu', size=256, pose_style=0):
    save_dir = os.path.join(result_dir, strftime("%Y_%m_%d_%H.%M.%S"))
    os.makedirs(save_dir, exist_ok=True)

    # モデルパス初期化
    sadtalker_paths = init_path(checkpoint_dir, os.path.join(os.path.dirname(__file__), 'src/config'), size, False, 'crop')

    preprocess_model = CropAndExtract(sadtalker_paths, device)
    audio_to_coeff = Audio2Coeff(sadtalker_paths, device)
    animate_from_coeff = AnimateFromCoeff(sadtalker_paths, device)

    # 画像→3DMM
    first_frame_dir = os.path.join(save_dir, 'first_frame')
    os.makedirs(first_frame_dir, exist_ok=True)
    first_coeff_path, crop_pic_path, crop_info = preprocess_model.generate(source_image, first_frame_dir, 'crop', source_image_flag=True, pic_size=size)
    if first_coeff_path is None:
        raise RuntimeError("Failed to extract coefficients from image.")

    # 音声→係数
    batch = get_data(first_coeff_path, driven_audio, device, None, still=False)
    coeff_path = audio_to_coeff.generate(batch, save_dir, pose_style, ref_pose_coeff_path=None)

    # アニメーション生成
    data = get_facerender_data(coeff_path, crop_pic_path, first_coeff_path, driven_audio, batch_size=2,
                               input_yaw_list=None, input_pitch_list=None, input_roll_list=None,
                               expression_scale=1.0, still_mode=False, preprocess='crop', size=size)

    result_temp_path = animate_from_coeff.generate(data, save_dir, source_image, crop_info,
                                                   enhancer=None, background_enhancer=None, preprocess='crop', img_size=size)

    # ファイル名確定 & 移動
    final_path = os.path.join(save_dir, "output.mp4")
    shutil.move(result_temp_path, final_path)

    return final_path
