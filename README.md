# WAN 2.2 Short Video Generator

WAN 2.2 GGUF 모델과 ComfyUI를 사용한 Short 동영상 생성 애플리케이션입니다.
Apple Silicon (M4 Pro) MPS 가속을 지원합니다.

## 아키텍처

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React Frontend │────▶│  FastAPI Backend │────▶│    ComfyUI      │
│   (localhost:8000)│     │  (localhost:8000)│     │ (localhost:8188)│
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  WAN 2.2 GGUF   │
                                                │  (Q4_K_S ~18GB) │
                                                └─────────────────┘
```

## 기술 스택

- **Frontend**: React + Vite (JavaScript)
- **Backend**: Python FastAPI (ComfyUI API 클라이언트)
- **AI Engine**: ComfyUI + ComfyUI-GGUF
- **Model**: WAN 2.2 T2V A14B GGUF (Q4_K_S 양자화)

## 기능

- 텍스트 프롬프트로 동영상 생성
- 480P 해상도 지원 (GGUF 최적화):
  - Portrait (480x832) - 9:16 비율
  - Landscape (832x480) - 16:9 비율
- 다양한 생성 옵션:
  - Negative Prompt
  - 프레임 수 (17-129)
  - Inference Steps (10-100)
  - Guidance Scale (1.0-20.0)
  - FPS (8-30)
  - Seed 설정

## 요구사항

- **Python**: 3.12.11
- **Node.js**: 18+
- **메모리**: 24GB+ (Apple Silicon 통합 메모리)
- **저장공간**: ~25GB (모델 파일)

## 설치 방법

### 1. 프로젝트 클론 후 의존성 설치

```bash
# Backend 가상환경 (이미 설치됨)
source venv/bin/activate
pip install -r backend/requirements.txt

# ComfyUI 가상환경 (이미 설치됨)
cd comfyui
source venv/bin/activate
pip install -r requirements.txt

# Frontend 빌드 (이미 빌드됨)
cd frontend
npm install
npm run build
```

### 2. 모델 다운로드

```bash
./scripts/download-models.sh
```

또는 수동으로:

```bash
cd comfyui
source venv/bin/activate

# HighNoise 모델 (~8.75GB)
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "HighNoise/*Q4_K_S*" \
    --local-dir ./models/diffusion_models

# LowNoise 모델 (~8.75GB)
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "LowNoise/*Q4_K_S*" \
    --local-dir ./models/diffusion_models

# VAE
huggingface-cli download QuantStack/Wan2.2-T2V-A14B-GGUF \
    --include "VAE/*" \
    --local-dir ./models/vae

# Text Encoder
huggingface-cli download Comfy-Org/Wan_2.1_ComfyUI_repackaged \
    --include "split_files/text_encoders/*" \
    --local-dir ./models/text_encoders
```

## 실행 방법

### 터미널 1: ComfyUI 시작

```bash
./scripts/start-comfyui.sh
# 또는
cd comfyui && source venv/bin/activate && python main.py --listen
```

### 터미널 2: Backend 시작

```bash
./scripts/start-backend.sh
# 또는
cd backend && source ../venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 브라우저에서 접속

- **웹 UI**: http://localhost:8000
- **ComfyUI**: http://localhost:8188 (선택사항)

## 사용 방법

1. ComfyUI와 Backend 서버 시작
2. 브라우저에서 http://localhost:8000 접속
3. "Connect" 버튼 클릭하여 ComfyUI 연결 확인
4. 프롬프트 입력
5. 비율 및 옵션 설정
6. "Generate Video" 클릭
7. 생성된 동영상 확인 (첫 실행 시 모델 로딩으로 시간 소요)

## 프로젝트 구조

```
short-generator/
├── backend/
│   ├── app/
│   │   ├── comfyui_client.py  # ComfyUI API 클라이언트
│   │   ├── workflow_builder.py # 워크플로우 빌더
│   │   ├── workflows/          # ComfyUI 워크플로우 JSON
│   │   ├── main.py             # FastAPI 앱
│   │   └── models.py           # Pydantic 모델
│   └── requirements.txt
├── comfyui/                    # ComfyUI 설치 디렉토리
│   ├── custom_nodes/
│   │   └── ComfyUI-GGUF/       # GGUF 지원 노드
│   ├── models/
│   │   ├── diffusion_models/   # GGUF 모델
│   │   ├── text_encoders/      # 텍스트 인코더
│   │   └── vae/                # VAE
│   └── venv/
├── frontend/
│   ├── src/
│   │   └── App.jsx             # 메인 컴포넌트
│   └── dist/                   # 빌드 결과물
├── outputs/                    # 생성된 동영상
├── scripts/
│   ├── start-comfyui.sh       # ComfyUI 시작
│   ├── start-backend.sh       # Backend 시작
│   └── download-models.sh     # 모델 다운로드
└── venv/                       # Backend 가상환경
```

## API 엔드포인트

- `GET /api/health` - 서버 및 ComfyUI 상태 확인
- `GET /api/status` - 생성 진행 상태
- `POST /api/load-model` - ComfyUI 연결 확인
- `POST /api/generate` - 동영상 생성
- `GET /api/videos` - 생성된 동영상 목록
- `DELETE /api/videos/{filename}` - 동영상 삭제

## 성능 참고

- **M4 Pro (24GB)**: 480P 81프레임 생성에 약 5-10분 예상
- Q4_K_S 양자화로 약 18GB VRAM 사용
- 첫 실행 시 모델 로딩에 추가 시간 소요

## 문제 해결

### ComfyUI 연결 실패
- ComfyUI가 실행 중인지 확인: `http://localhost:8188`
- `--listen` 옵션으로 실행했는지 확인

### MPS 관련 오류
- GGUF 모델 사용 필수 (safetensors는 MPS에서 오류 발생)
- ComfyUI-GGUF 커스텀 노드 설치 확인

### 메모리 부족
- 해상도를 320x320으로 낮춰서 테스트
- 프레임 수 줄이기
