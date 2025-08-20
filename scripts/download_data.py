#!/usr/bin/env python3
"""
배포 환경에서 FAQ 데이터를 다운로드하는 스크립트
"""

import os
import requests
import zipfile
from pathlib import Path

def download_faq_data():
    """FAQ 데이터를 다운로드합니다."""
    
    # data 디렉토리 생성
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # 데이터 파일 경로
    pkl_path = data_dir / "final_result.pkl"
    
    # 이미 존재하면 스킵
    if pkl_path.exists():
        print(f"✅ 데이터 파일이 이미 존재합니다: {pkl_path}")
        return
    
    # 환경 변수에서 다운로드 URL 확인
    download_url = os.getenv("FAQ_DATA_URL")
    
    if not download_url:
        print("❌ FAQ_DATA_URL 환경 변수가 설정되지 않았습니다.")
        print("다음 중 하나를 선택하세요:")
        print("1. FAQ_DATA_URL 환경 변수 설정")
        print("2. 수동으로 data/final_result.pkl 파일 추가")
        return
    
    try:
        print(f"📥 데이터 다운로드 중: {download_url}")
        
        # 데이터 다운로드
        response = requests.get(download_url, stream=True)
        response.raise_for_status()
        
        # 파일 저장
        with open(pkl_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"✅ 데이터 다운로드 완료: {pkl_path}")
        
    except Exception as e:
        print(f"❌ 데이터 다운로드 실패: {e}")
        print("수동으로 data/final_result.pkl 파일을 추가해주세요.")

if __name__ == "__main__":
    download_faq_data()
