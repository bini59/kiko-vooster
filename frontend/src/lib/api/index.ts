/**
 * API 모듈 통합 인덱스
 *
 * 모든 API 서비스들을 쉽게 import할 수 있도록 re-export
 */

// Base API Client
export {
  getApiClient,
  setApiClient,
  ApiError,
  NetworkError,
  AuthError,
} from "./client.js";

// Domain-specific API services
export { getScriptsApi, setScriptsApi, scriptsApi } from "./scripts.js";

export { getAudioApi, setAudioApi, audioApi } from "./audio.js";

export { getSyncApi, setSyncApi, syncApi } from "./sync.js";

// 모든 API 서비스를 포함하는 통합 객체
export const api = {
  scripts: () => import("./scripts.js").then((m) => m.scriptsApi),
  audio: () => import("./audio.js").then((m) => m.audioApi),
  sync: () => import("./sync.js").then((m) => m.syncApi),
};

// 타입 exports (필요한 경우)
export type { ApiClient } from "./client.js";
