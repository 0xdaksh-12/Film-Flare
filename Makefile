.PHONY: server client install

server:
	cd server && uv run uvicorn src:app --host 0.0.0.0 --port 8000 --reload

client:
	cd client && pnpm run dev

install:
	cd server && uv sync
	cd client && pnpm install

seed:
	cd server && uv run python -m src.core.seed