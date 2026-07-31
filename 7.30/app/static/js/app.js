/* Insurance AI - 前端 SPA 主逻辑（P0-06 占位，P1-15 富化） */

(function () {
  "use strict";

  // ========== DOM 引用 ==========
  var loginPage = document.getElementById("login-page");
  var registerPage = document.getElementById("register-page");
  var appPage = document.getElementById("app-page");
  var loginForm = document.getElementById("login-form");
  var loginError = document.getElementById("login-error");
  var registerForm = document.getElementById("register-form");
  var registerError = document.getElementById("register-error");
  var registerSuccess = document.getElementById("register-success");
  var navMenu = document.getElementById("nav-menu");
  var currentUserEl = document.getElementById("current-user");
  var appContent = document.getElementById("app-content");
  var btnLogout = document.getElementById("btn-logout");

  var currentUser = null;

  // ========== 路由 ==========
  var routes = {
    upload: "数据上传",
    customers: "客户列表",
    statistics: "数据统计",
    quality: "数据质量",
    eda: "EDA 可视化",
    train: "模型训练",
    experiments: "实验记录",
    predict: "概率预测",
    model_viz: "模型评估",
    export: "模型导出",
    import: "模型导入",
    targets: "高潜客户",
    generate: "生成邮件",
    records: "邮件记录",
    prompt: "Prompt 模板",
    logs: "操作日志",
  };

  // ========== 菜单 ==========
  var adminMenu = [
    { label: "数据上传", hash: "upload" },
    { label: "客户列表", hash: "customers" },
    { label: "数据统计", hash: "statistics" },
    { label: "数据质量", hash: "quality" },
    { label: "EDA 可视化", hash: "eda" },
    { label: "模型训练", hash: "train" },
    { label: "实验记录", hash: "experiments" },
    { label: "概率预测", hash: "predict" },
    { label: "模型评估", hash: "model_viz" },
    { label: "模型导入导出", hash: "import" },
    { label: "高潜客户", hash: "targets" },
    { label: "生成邮件", hash: "generate" },
    { label: "邮件记录", hash: "records" },
    { label: "Prompt 模板", hash: "prompt" },
    { label: "操作日志", hash: "logs" },
  ];

  var userMenu = [
    { label: "客户列表", hash: "customers" },
    { label: "数据统计", hash: "statistics" },
    { label: "数据质量", hash: "quality" },
    { label: "EDA 可视化", hash: "eda" },
    { label: "实验记录", hash: "experiments" },
    { label: "概率预测", hash: "predict" },
    { label: "模型评估", hash: "model_viz" },
    { label: "高潜客户", hash: "targets" },
    { label: "生成邮件", hash: "generate" },
    { label: "邮件记录", hash: "records" },
    { label: "Prompt 模板", hash: "prompt" },
  ];

  function showPage(page) {
    loginPage.classList.add("d-none");
    registerPage.classList.add("d-none");
    appPage.classList.add("d-none");
    page.classList.remove("d-none");
  }

  function renderMenu() {
    var menu = currentUser && currentUser.role === "admin" ? adminMenu : userMenu;
    navMenu.innerHTML = "";
    menu.forEach(function (item) {
      var li = document.createElement("li");
      li.className = "nav-item";
      var a = document.createElement("a");
      a.className = "nav-link";
      a.href = "#" + item.hash;
      a.textContent = item.label;
      li.appendChild(a);
      navMenu.appendChild(li);
    });
  }

  function handleRoute() {
    var hash = window.location.hash.slice(1) || "";
    if (!hash) return;
    var label = routes[hash] || hash;
    appContent.innerHTML = '<div class="alert alert-info">' + label + ' 功能开发中，敬请期待。</div>';
  }

  // ========== 登录 ==========
  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    loginError.classList.add("d-none");
    var username = document.getElementById("username").value.trim();
    var password = document.getElementById("password").value.trim();
    if (!username || !password) {
      loginError.textContent = "请输入用户名和密码";
      loginError.classList.remove("d-none");
      return;
    }
    var res = await api("POST", "/auth/login", { username: username, password: password });
    if (res.code !== 0) {
      loginError.textContent = res.message;
      loginError.classList.remove("d-none");
      return;
    }
    setToken(res.data.access_token);
    currentUser = res.data.user;
    currentUserEl.textContent = currentUser.username + " (" + currentUser.role + ")";
    renderMenu();
    showPage(appPage);
    window.location.hash = "";
  });

  // ========== 注册 ==========
  registerForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    registerError.classList.add("d-none");
    registerSuccess.classList.add("d-none");
    var username = document.getElementById("reg-username").value.trim();
    var password = document.getElementById("reg-password").value.trim();
    if (!username || !password) {
      registerError.textContent = "请输入用户名和密码";
      registerError.classList.remove("d-none");
      return;
    }
    var res = await api("POST", "/auth/register", { username: username, password: password });
    if (res.code !== 0) {
      registerError.textContent = res.message;
      registerError.classList.remove("d-none");
      return;
    }
    registerSuccess.textContent = "注册成功！请登录。";
    registerSuccess.classList.remove("d-none");
    setTimeout(function () { showPage(loginPage); }, 1500);
  });

  // ========== 退出 ==========
  btnLogout.addEventListener("click", function () {
    clearToken();
    currentUser = null;
    showPage(loginPage);
    window.location.hash = "";
  });

  // ========== 页面切换 ==========
  document.getElementById("show-register").addEventListener("click", function (e) {
    e.preventDefault();
    showPage(registerPage);
  });
  document.getElementById("show-login").addEventListener("click", function (e) {
    e.preventDefault();
    showPage(loginPage);
  });

  // ========== Hash 路由 ==========
  window.addEventListener("hashchange", handleRoute);
  handleRoute();

  // ========== 初始状态 ==========
  showPage(loginPage);
})();
