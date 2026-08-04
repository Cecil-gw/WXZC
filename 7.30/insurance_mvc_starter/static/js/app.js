const Auth = {
  TOKEN_KEY: "insurance_mvc_token",
  USER_KEY: "insurance_mvc_user",

  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  },

  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
  },

  removeToken() {
    localStorage.removeItem(this.TOKEN_KEY);
  },

  getUser() {
    const user = localStorage.getItem(this.USER_KEY);
    return user ? JSON.parse(user) : null;
  },

  setUser(user) {
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));
  },

  removeUser() {
    localStorage.removeItem(this.USER_KEY);
  },

  isLoggedIn() {
    return !!this.getToken();
  },

  getAuthHeader() {
    const token = this.getToken();
    return token ? { Authorization: "Bearer " + token } : {};
  },

  logout() {
    this.removeToken();
    this.removeUser();
  },
};

const api = {
  async get(url, options = {}) {
    return this.request(url, { ...options, method: "GET" });
  },

  async post(url, data = null, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    return this.request(url, {
      ...options,
      method: "POST",
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async put(url, data = null, options = {}) {
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };
    return this.request(url, {
      ...options,
      method: "PUT",
      headers,
      body: data ? JSON.stringify(data) : undefined,
    });
  },

  async delete(url, options = {}) {
    return this.request(url, { ...options, method: "DELETE" });
  },

  async request(url, options = {}) {
    const headers = {
      ...Auth.getAuthHeader(),
      ...(options.headers || {}),
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      Auth.logout();
      window.location.href = "/login";
      throw new Error("未授权，请重新登录");
    }

    if (!response.ok) {
      const text = await response.text();
      let message = "请求失败";
      try {
        const data = JSON.parse(text);
        message = data.message || data.detail || message;
      } catch (_) {
        message = text || message;
      }
      const error = new Error(message);
      error.status = response.status;
      throw error;
    }

    return response.json();
  },
};

function updateNavbarAuthUI() {
  const navAuth = document.getElementById("nav-auth");
  const navRegister = document.getElementById("nav-register");
  const navUser = document.getElementById("nav-user");
  const navUpload = document.getElementById("nav-upload");
  const userName = document.getElementById("user-name");
  const userRole = document.getElementById("user-role");

  const user = Auth.getUser();

  if (user) {
    navAuth.style.display = "none";
    navRegister.style.display = "none";
    navUser.style.display = "";
    userName.textContent = user.username || "用户";
    userRole.textContent = user.role || "user";

    if (user.role === "admin") {
      navUpload.style.display = "";
    } else {
      navUpload.style.display = "none";
    }
  } else {
    navAuth.style.display = "";
    navRegister.style.display = "";
    navUser.style.display = "none";
    navUpload.style.display = "none";
  }
}

function handleLoginForm() {
  const form = document.getElementById("login-form");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;

    if (!username || !password) {
      alert("请填写用户名和密码");
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> 登录中...';

    try {
      const res = await api.post("/api/v1/auth/login", { username, password });

      if (res.code === 0) {
        const data = res.data;
        Auth.setToken(data.access_token);
        Auth.setUser(data.user);
        window.location.href = "/";
      } else {
        alert("登录失败：" + (res.message || "未知错误"));
      }
    } catch (err) {
      alert("登录失败：" + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="bi bi-box-arrow-in-right"></i> 登录';
    }
  });
}

function handleRegisterForm() {
  const form = document.getElementById("register-form");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value;
    const confirmPassword = document.getElementById("confirm_password").value;

    if (!username || !password || !confirmPassword) {
      alert("请填写所有字段");
      return;
    }

    if (password.length < 6) {
      alert("密码至少 6 个字符");
      return;
    }

    if (password !== confirmPassword) {
      alert("两次输入的密码不一致");
      return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML =
      '<span class="spinner-border spinner-border-sm"></span> 注册中...';

    try {
      const res = await api.post("/api/v1/auth/register", {
        username,
        password,
      });

      if (res.code === 0) {
        const data = res.data;
        Auth.setToken(data.access_token);
        Auth.setUser(data.user);
        window.location.href = "/";
      } else {
        alert("注册失败：" + (res.message || "未知错误"));
      }
    } catch (err) {
      alert("注册失败：" + err.message);
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = '<i class="bi bi-person-plus"></i> 注册账号';
    }
  });
}

function handleLogout() {
  const btn = document.getElementById("logout-btn");
  if (!btn) return;

  btn.addEventListener("click", function (e) {
    e.preventDefault();
    if (confirm("确定要退出登录吗？")) {
      Auth.logout();
      window.location.href = "/login";
    }
  });
}

function initPage() {
  updateNavbarAuthUI();
  handleLoginForm();
  handleRegisterForm();
  handleLogout();

  const protectedPages = ["/", "/dashboard", "/customers", "/upload"];
  const currentPath = window.location.pathname;

  if (protectedPages.includes(currentPath) && !Auth.isLoggedIn()) {
    window.location.href = "/login";
    return;
  }

  if (
    (currentPath === "/login" || currentPath === "/register") &&
    Auth.isLoggedIn()
  ) {
    window.location.href = "/";
    return;
  }
}

document.addEventListener("DOMContentLoaded", initPage);
