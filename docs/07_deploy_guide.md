# Docker 기반 배포 가이드 (v2.0)

## 1) 구성
- Postgres: 회사/계정과목/분개/증빙/보고서/ML 결과
- Redis: RQ(Redis Queue) 작업큐
- MinIO: (옵션) S3 호환 저장소
- API Server(Flask), Worker(RQ), Web Admin/Client(정적 파일, `python -m http.server`)

## 2) 로컬 실행 (Docker Compose)
```bash
cp .env.example .env
python scripts/dev_up.py     # docker compose up -d --build
python scripts/db_migrate.py
python scripts/db_seed.py
```
- API: http://localhost:8081
- Web Admin: http://localhost:3002
- Web Client: http://localhost:3001

컨테이너 네트워크에서는 `docker-compose.yml`이 `POSTGRES_HOST=postgres`, `REDIS_HOST=redis`로 자동 오버라이드합니다.
(.env의 `localhost` 기본값은 호스트에서 직접 `python apps/api-server/wsgi.py`를 실행하는 개발 모드용입니다.)

## 3) EasyOCR(실제 DL 모델) 활성화
기본 이미지는 가벼운 `fixture` OCR로 빌드됩니다. 실제 EasyOCR을 쓰려면:
```bash
docker compose -f infra/docker/docker-compose.yml build --build-arg WITH_OCR=1 worker
```
그리고 `.env`에서 `OCR_PROVIDER=easyocr`로 변경하세요. (최초 실행 시 언어 가중치 다운로드로 네트워크 필요)

## 4) 운영 팁
- Worker 동시성: 여러 worker 컨테이너를 띄우거나 `run_worker.py`를 복수 프로세스로 실행
- 재시도: `pdf_reports.status`가 `failed`인 건은 `error_log` 확인 후 재요청
- 스토리지:
  - MVP 기본: local 디렉터리 저장(`storage/pdfs`, `storage/uploads`)
  - 확장: MinIO/S3 저장으로 전환 가능(현재 코드는 local 경로만 구현, `STORAGE_MODE` 값은 예약됨)
- DART 캐시: `DART_CACHE_DIR`(기본 `.cache/dart`)에 corpCode.xml을 24시간 캐시하여 반복 다운로드를 방지합니다.

## 5) 개별 이미지 빌드
```bash
docker compose -f infra/docker/docker-compose.yml build api worker web-admin web-client
```
4개 이미지 모두 독립적으로 빌드/기동 가능합니다.
