/* Insurance AI - API 请求封装（P0-06 占位，P1-15 富化） */

const API_BASE = "/api/v1";

/** 从 localStorage 读取 Token */
function getToken() {
  return localStorage.getItem("access_token");
}

/** 保存 Token */
function setToken(token) {
  localStorage.setItem("access_token", token);
}

/** 清除 Token */
function clearToken() {
  localStorage.removeItem("access_token");
}

/**
 * 统一请求封装。
 * @param {string} method  GET | POST | PUT | PATCH | DELETE
 * @param {string} path    相对 /api/v1 的路径，如 "/auth/login"
 * @param {object} [body]  请求体（JSON）
 * @returns {Promise<object>} 响应 JSON
 */
async function api(method, path, body) {
  const headers = { "Content-Type": "application/json" };
  const token = getToken();
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }
  const opts = { method, headers };
  if (body) {
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(API_BASE + path, opts);
  const json = await res.json();
  if (json.code === 1002) {
    clearToken();
  }
  return json;
}
