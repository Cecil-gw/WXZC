/* Insurance AI - API 请求封装（P1-15）。
 *
 * 三件事集中在这里，页面代码不再重复：
 * 1. 自动注入 Authorization（PRD §3.7）；
 * 2. 统一解包 {code, message, data}；
 * 3. code=1002 时清 Token 并跳回登录页 —— Token 过期后继续留在主界面
 *    会让后续每个请求都静默失败，用户看到的是「页面坏了」而不是「请重新登录」。
 */

const API_BASE = "/api/v1";

/** 401 回调，由 app.js 注册（避免 api.js 反向依赖 DOM） */
let onUnauthorized = null;
function setUnauthorizedHandler(fn) {
  onUnauthorized = fn;
}

function getToken() {
  return localStorage.getItem("access_token");
}
function setToken(token) {
  localStorage.setItem("access_token", token);
}
function clearToken() {
  localStorage.removeItem("access_token");
}
function getCachedUser() {
  try {
    return JSON.parse(localStorage.getItem("current_user") || "null");
  } catch (e) {
    return null;
  }
}
function setCachedUser(user) {
  localStorage.setItem("current_user", JSON.stringify(user));
}
function clearCachedUser() {
  localStorage.removeItem("current_user");
}

function authHeaders(extra) {
  const headers = Object.assign({}, extra || {});
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  return headers;
}

function handleUnauthorized(json) {
  if (json && json.code === 1002) {
    clearToken();
    clearCachedUser();
    if (onUnauthorized) onUnauthorized();
  }
  return json;
}

/**
 * JSON 请求。
 * @param {string} method GET|POST|PUT|PATCH|DELETE
 * @param {string} path   相对 /api/v1，如 "/auth/login"
 * @param {object} [body]
 * @returns {Promise<{code:number,message:string,data:*}>}
 */
async function api(method, path, body) {
  const opts = {
    method: method,
    headers: authHeaders({ "Content-Type": "application/json" }),
  };
  if (body !== undefined && body !== null) opts.body = JSON.stringify(body);
  let res;
  try {
    res = await fetch(API_BASE + path, opts);
  } catch (e) {
    // 网络层失败也走统一结构，页面无需区分「请求没发出去」和「后端报错」
    return { code: -1, message: "网络请求失败: " + e.message, data: null };
  }
  let json;
  try {
    json = await res.json();
  } catch (e) {
    return { code: -1, message: "响应解析失败 (HTTP " + res.status + ")", data: null };
  }
  return handleUnauthorized(json);
}

/**
 * 文件上传（multipart/form-data）。
 * 不能手写 Content-Type —— 必须让浏览器自己补 boundary，否则后端解析不出文件。
 */
async function apiUpload(path, file, fields) {
  const fd = new FormData();
  fd.append("file", file);
  if (fields) Object.keys(fields).forEach((k) => fd.append(k, fields[k]));
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method: "POST",
      headers: authHeaders(),
      body: fd,
    });
  } catch (e) {
    return { code: -1, message: "网络请求失败: " + e.message, data: null };
  }
  if (res.status === 413) {
    return { code: 1001, message: "上传文件超过50MB限制", data: null };
  }
  let json;
  try {
    json = await res.json();
  } catch (e) {
    return { code: -1, message: "响应解析失败 (HTTP " + res.status + ")", data: null };
  }
  return handleUnauthorized(json);
}

/**
 * 二进制下载（模型导出）。
 * 后端出错时返回的是 JSON 而非文件流，因此按 content-type 分流。
 */
async function apiDownload(path, filename) {
  let res;
  try {
    res = await fetch(API_BASE + path, { headers: authHeaders() });
  } catch (e) {
    return { code: -1, message: "网络请求失败: " + e.message, data: null };
  }
  const ct = res.headers.get("content-type") || "";
  if (ct.indexOf("application/json") >= 0) {
    return handleUnauthorized(await res.json());
  }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return { code: 0, message: "success", data: { filename: filename } };
}

/** 把对象拼成 query string，跳过空值 */
function qs(params) {
  const parts = [];
  Object.keys(params || {}).forEach(function (k) {
    const v = params[k];
    if (v === undefined || v === null || v === "") return;
    parts.push(encodeURIComponent(k) + "=" + encodeURIComponent(v));
  });
  return parts.length ? "?" + parts.join("&") : "";
}