/* Insurance AI - 前端 SPA 主逻辑（P1-15）。
 *
 * 结构：工具函数 → 菜单/路由 → 各功能页 render 函数 → 认证与启动。
 * 菜单按 PRD §3.7 分组：普通用户 7 项，admin 额外 4 项（共 11 项）。
 * 分组依据是后端鉴权边界 —— admin-only 的接口不放进普通用户菜单，
 * 避免点进去只看到 403。
 */

(function () {
  "use strict";

  var loginPage = document.getElementById("login-page");
  var registerPage = document.getElementById("register-page");
  var appPage = document.getElementById("app-page");
  var navMenu = document.getElementById("nav-menu");
  var currentUserEl = document.getElementById("current-user");
  var appContent = document.getElementById("app-content");
  var toastArea = document.getElementById("toast-area");

  var currentUser = null;

  // ============ 工具 ============

  function esc(v) {
    if (v === null || v === undefined) return "";
    return String(v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function num(v, digits) {
    if (v === null || v === undefined || v === "") return "-";
    var n = Number(v);
    if (isNaN(n)) return esc(v);
    return digits === undefined ? n.toLocaleString() : n.toFixed(digits);
  }

  function pct(v) {
    if (v === null || v === undefined) return "-";
    return (Number(v) * 100).toFixed(2) + "%";
  }

  function toast(message, kind) {
    // 确保 toastArea 存在
    if (!toastArea) {
      toastArea = document.getElementById("toast-area");
      if (!toastArea) {
        // 如果还不存在，创建一个
        toastArea = document.createElement("div");
        toastArea.id = "toast-area";
        toastArea.className = "position-fixed top-3 end-3 z-3 p-3";
        toastArea.style.maxWidth = "400px";
        document.body.appendChild(toastArea);
      }
    }
    var el = document.createElement("div");
    el.className =
      "alert alert-" + (kind || "info") + " alert-dismissible shadow-sm py-2";
    el.innerHTML =
      '<span class="small">' +
      esc(message) +
      "</span>" +
      '<button type="button" class="btn-close btn-sm" data-bs-dismiss="alert"></button>';
    toastArea.appendChild(el);
    setTimeout(function () {
      if (el.parentNode) el.parentNode.removeChild(el);
    }, 4200);
  }

  function unwrap(res, silent) {
    if (res && res.code === 0) return res.data === undefined ? {} : res.data;
    if (!silent) toast((res && res.message) || "请求失败", "danger");
    return null;
  }

  function setBusy(el, text) {
    if (!el) return;
    el.dataset.orig = el.innerHTML;
    el.disabled = true;
    el.innerHTML =
      '<span class="spinner-border spinner-border-sm me-1"></span>' +
      esc(text || "处理中");
  }
  function clearBusy(el) {
    if (!el || !el.dataset.orig) return;
    el.innerHTML = el.dataset.orig;
    el.disabled = false;
    delete el.dataset.orig;
  }

  function loading(msg) {
    if (!appContent) {
      appContent = document.getElementById("app-content");
    }
    if (appContent) {
      appContent.innerHTML =
        '<div class="empty"><span class="spinner-border spinner-border-sm me-2"></span>' +
        esc(msg || "加载中") +
        "</div>";
    }
  }

  function head(title, actionsHtml) {
    return (
      '<div class="page-head"><h5>' +
      esc(title) +
      "</h5>" +
      '<div class="actions">' +
      (actionsHtml || "") +
      "</div></div>"
    );
  }

  function setContent(html) {
    if (!appContent) {
      appContent = document.getElementById("app-content");
    }
    if (appContent) {
      appContent.innerHTML = html;
    }
  }

  function metric(label, value) {
    return (
      '<div class="col-6 col-md-3 mb-2"><div class="metric">' +
      '<div class="label">' +
      esc(label) +
      "</div>" +
      '<div class="value">' +
      value +
      "</div></div></div>"
    );
  }

  function emptyRow(cols, msg) {
    return (
      '<tr><td colspan="' +
      cols +
      '" class="empty">' +
      esc(msg || "暂无数据") +
      "</td></tr>"
    );
  }

  function pager(meta, onGo) {
    if (!meta || !meta.pages || meta.pages <= 1) {
      return (
        '<span class="text-muted small">共 ' +
        num(meta && meta.total) +
        " 条</span>"
      );
    }
    var wrap = document.createElement("div");
    wrap.className = "d-flex align-items-center gap-2";
    wrap.innerHTML =
      '<span class="text-muted small">共 ' +
      num(meta.total) +
      " 条 · 第 " +
      meta.page +
      " / " +
      meta.pages +
      " 页</span>" +
      '<div class="btn-group btn-group-sm">' +
      '<button class="btn btn-outline-secondary" data-go="prev" title="上一页"' +
      (meta.page <= 1 ? " disabled" : "") +
      ">&laquo;</button>" +
      '<button class="btn btn-outline-secondary" data-go="next" title="下一页"' +
      (meta.page >= meta.pages ? " disabled" : "") +
      ">&raquo;</button></div>";
    wrap.addEventListener("click", function (e) {
      var b = e.target.closest("button[data-go]");
      if (!b) return;
      onGo(b.dataset.go === "prev" ? meta.page - 1 : meta.page + 1);
    });
    return wrap;
  }

  function mount(sel, content) {
    if (!appContent) {
      appContent = document.getElementById("app-content");
    }
    if (!appContent) return;
    var box = appContent.querySelector(sel);
    if (!box) return;
    box.innerHTML = "";
    if (typeof content === "string") box.innerHTML = content;
    else if (content) box.appendChild(content);
  }

  function isAdmin() {
    return currentUser && currentUser.role === "admin";
  }

  function fmtDate(s) {
    if (!s) return "-";
    try {
      return new Date(s).toLocaleString("zh-CN");
    } catch (e) {
      return s;
    }
  }

  function fmtProb(v) {
    if (v === null || v === undefined || v === "") return "-";
    return (Number(v) * 100).toFixed(1) + "%";
  }

  function statusBadge(status) {
    var map = {
      pending: "bg-warning",
      generated: "bg-success",
      failed: "bg-danger",
      sent: "bg-info",
    };
    var cls = map[status] || "bg-secondary";
    return (
      '<span class="badge ' + cls + '">' + esc(status || "unknown") + "</span>"
    );
  }

  // ============ 菜单配置 ============

  var userMenus = [
    { key: "customers", label: "客户列表", icon: "👥" },
    { key: "statistics", label: "数据统计", icon: "📊" },
    { key: "quality", label: "数据质量", icon: "✅" },
    { key: "eda", label: "EDA 可视化", icon: "📈" },
    { key: "experiments", label: "模型实验", icon: "🧪" },
    { key: "targets", label: "高潜客户", icon: "🎯" },
    { key: "emails", label: "邮件中心", icon: "📧" },
  ];

  var adminMenus = [
    { key: "upload", label: "数据上传", icon: "📁" },
    { key: "train", label: "模型训练", icon: "🤖" },
    { key: "modelmgmt", label: "模型管理", icon: "⚙️" },
    { key: "logs", label: "操作日志", icon: "📋" },
  ];

  function buildMenus() {
    if (!navMenu) {
      navMenu = document.getElementById("nav-menu");
    }
    if (!navMenu) return;
    var menus = userMenus.slice();
    if (isAdmin()) menus = menus.concat(adminMenus);
    navMenu.innerHTML = "";
    menus.forEach(function (m) {
      var li = document.createElement("li");
      li.className = "nav-item";
      var a = document.createElement("a");
      a.className = "nav-link";
      a.href = "#/" + m.key;
      a.textContent = m.icon + " " + m.label;
      li.appendChild(a);
      navMenu.appendChild(li);
    });
  }

  function setActiveMenu(key) {
    if (!navMenu) {
      navMenu = document.getElementById("nav-menu");
    }
    if (!navMenu) return;
    var links = navMenu.querySelectorAll(".nav-link");
    links.forEach(function (a) {
      if (a.getAttribute("href") === "#/" + key) a.classList.add("active");
      else a.classList.remove("active");
    });
  }

  // ============ 路由 ============

  function currentRoute() {
    var h = location.hash || "#/customers";
    return h.replace(/^#\//, "");
  }

  function navigate(key) {
    location.hash = "#/" + key;
  }

  function route() {
    var key = currentRoute();
    setActiveMenu(key);
    var handler = pages[key] || pages.customers;
    try {
      handler();
    } catch (e) {
      setContent(
        '<div class="alert alert-danger m-3">页面渲染出错: ' +
          esc(e.message) +
          '<br><small class="text-muted">' +
          esc(e.stack) +
          "</small></div>",
      );
      console.error("页面渲染错误:", e);
    }
  }

  // ============ 页面渲染 ============

  var pages = {};

  // ---- 客户列表 ----
  pages.customers = function () {
    loading("加载客户列表...");
    renderCustomers(1, {});
  };

  function renderCustomers(page, filters) {
    var params = Object.assign({ page: page, per_page: 20 }, filters || {});
    api("GET", "/data/customers" + qs(params)).then(function (res) {
      var data = unwrap(res);
      if (!data) return;
      var rows = data.items || [];
      var cols = 13;

      var html = head(
        "客户列表",
        '<div class="filters" id="cust-filters">' +
          '<select class="form-select form-select-sm" id="f-gender"><option value="">全部性别</option><option>Male</option><option>Female</option></select>' +
          '<input class="form-control form-control-sm" id="f-kw" placeholder="年龄最小" style="width:90px">' +
          '<input class="form-control form-control-sm" id="f-kw2" placeholder="年龄最大" style="width:90px">' +
          '<select class="form-select form-select-sm" id="f-resp"><option value="">全部响应</option><option value="1">已响应</option><option value="0">未响应</option></select>' +
          '<button class="btn btn-sm btn-outline-primary" id="btn-filter">筛选</button>' +
          '<button class="btn btn-sm btn-outline-secondary" id="btn-reset">重置</button>' +
          "</div>" +
          '<div id="cust-pager"></div>',
      );

      html +=
        '<div class="table-wrap" style="overflow-x:auto"><table class="table table-hover table-sm"><thead><tr>' +
        '<th>ID</th><th>Gender</th><th class="num">Age</th><th class="num">Driving_License</th><th class="num">Region_Code</th>' +
        '<th class="num">Previously_Insured</th><th>Vehicle_Age</th><th>Vehicle_Damage</th><th class="num">Annual_Premium</th>' +
        '<th class="num">Policy_Sales_Channel</th><th class="num">Vintage</th><th>Response</th><th class="num">预测概率</th>' +
        "</tr></thead><tbody>";

      if (!rows.length) {
        html += emptyRow(cols, "暂无客户数据，请先上传 Excel 文件");
      } else {
        rows.forEach(function (c) {
          var resp =
            c.response === 1
              ? '<span class="badge bg-success">是</span>'
              : c.response === 0
                ? '<span class="badge bg-secondary">否</span>'
                : "-";
          html +=
            "<tr>" +
            "<td>" +
            esc(c.id) +
            "</td>" +
            "<td>" +
            esc(c.gender) +
            "</td>" +
            '<td class="num">' +
            num(c.age) +
            "</td>" +
            '<td class="num">' +
            num(c.driving_license) +
            "</td>" +
            '<td class="num">' +
            num(c.region_code) +
            "</td>" +
            '<td class="num">' +
            num(c.previously_insured) +
            "</td>" +
            "<td>" +
            esc(c.vehicle_age) +
            "</td>" +
            "<td>" +
            esc(c.vehicle_damage) +
            "</td>" +
            '<td class="num">' +
            num(c.annual_premium) +
            "</td>" +
            '<td class="num">' +
            num(c.policy_sales_channel) +
            "</td>" +
            '<td class="num">' +
            num(c.vintage) +
            "</td>" +
            "<td>" +
            resp +
            "</td>" +
            '<td class="num">' +
            fmtProb(c.predicted_prob) +
            "</td>" +
            "</tr>";
        });
      }
      html += "</tbody></table></div>";

      appContent.innerHTML = html;

      // pager
      mount(
        "#cust-pager",
        pager(
          { total: data.total, page: data.page, pages: data.pages },
          function (p) {
            var g = document.getElementById("f-gender").value;
            var a1 = document.getElementById("f-kw").value;
            var a2 = document.getElementById("f-kw2").value;
            var r = document.getElementById("f-resp").value;
            var f = {};
            if (g) f.gender = g;
            if (a1) f.age_min = a1;
            if (a2) f.age_max = a2;
            if (r) f.has_response = r;
            renderCustomers(p, f);
          },
        ),
      );

      // filter events
      document
        .getElementById("btn-filter")
        .addEventListener("click", function () {
          var g = document.getElementById("f-gender").value;
          var a1 = document.getElementById("f-kw").value;
          var a2 = document.getElementById("f-kw2").value;
          var r = document.getElementById("f-resp").value;
          var f = {};
          if (g) f.gender = g;
          if (a1) f.age_min = a1;
          if (a2) f.age_max = a2;
          if (r) f.has_response = r;
          renderCustomers(1, f);
        });
      document
        .getElementById("btn-reset")
        .addEventListener("click", function () {
          renderCustomers(1, {});
        });
    });
  }

  // ---- 数据统计 ----
  pages.statistics = function () {
    loading("加载统计数据...");
    api("GET", "/data/statistics").then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var html = head("数据统计");
      html += '<div class="row">';
      html += metric("总客户数", num(d.total));
      html += metric(
        "已响应",
        num(d.response_distribution && d.response_distribution["1"]),
      );
      html += metric(
        "未响应",
        num(d.response_distribution && d.response_distribution["0"]),
      );
      html += metric("平均年龄", num(d.age_stats && d.age_stats.avg, 1));
      html += "</div>";
      html += '<div class="row"><div class="col-12 col-md-6 mb-3">';
      html +=
        '<div class="card"><div class="card-body"><h6>性别分布</h6><table class="table table-sm"><thead><tr><th>性别</th><th class="num">数量</th></tr></thead><tbody>';
      if (d.gender_distribution) {
        Object.keys(d.gender_distribution).forEach(function (k) {
          html +=
            "<tr><td>" +
            esc(k) +
            '</td><td class="num">' +
            num(d.gender_distribution[k]) +
            "</td></tr>";
        });
      }
      html += "</tbody></table></div></div></div>";
      html += '<div class="col-12 col-md-6 mb-3">';
      html +=
        '<div class="card"><div class="card-body"><h6>响应分布</h6><table class="table table-sm"><thead><tr><th>状态</th><th class="num">数量</th></tr></thead><tbody>';
      if (d.response_distribution) {
        Object.keys(d.response_distribution).forEach(function (k) {
          html +=
            "<tr><td>" +
            (k === "1" ? "已响应" : "未响应") +
            '</td><td class="num">' +
            num(d.response_distribution[k]) +
            "</td></tr>";
        });
      }
      html += "</tbody></table></div></div></div></div>";
      html += '<div class="row"><div class="col-12 col-md-6 mb-3">';
      html +=
        '<div class="card"><div class="card-body"><h6>年龄统计</h6><table class="table table-sm"><tbody>';
      if (d.age_stats) {
        html +=
          '<tr><td>最小值</td><td class="num">' +
          num(d.age_stats.min) +
          "</td></tr>";
        html +=
          '<tr><td>最大值</td><td class="num">' +
          num(d.age_stats.max) +
          "</td></tr>";
        html +=
          '<tr><td>平均值</td><td class="num">' +
          num(d.age_stats.avg, 1) +
          "</td></tr>";
      }
      html += "</tbody></table></div></div></div></div>";
      appContent.innerHTML = html;
    });
  };

  // ---- 数据质量 ----
  pages.quality = function () {
    loading("加载数据质量报告...");
    api("GET", "/data/quality").then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var html = head("数据质量报告");
      html += '<div class="row">';
      html += metric("总行数", num(d.total_rows));
      html += metric("列数", num(d.total_cols));
      html += metric("重复行", num(d.duplicates));
      html += "</div>";

      if (d.dtypes) {
        html +=
          '<div class="card mb-3"><div class="card-body"><h6>字段类型</h6><table class="table table-sm"><thead><tr><th>字段</th><th>类型</th></tr></thead><tbody>';
        Object.keys(d.dtypes).forEach(function (k) {
          html +=
            "<tr><td>" + esc(k) + "</td><td>" + esc(d.dtypes[k]) + "</td></tr>";
        });
        html += "</tbody></table></div></div>";
      }

      if (d.missing_values) {
        html +=
          '<div class="card mb-3"><div class="card-body"><h6>缺失值详情</h6><table class="table table-sm"><thead><tr><th>字段</th><th class="num">缺失数</th></tr></thead><tbody>';
        Object.keys(d.missing_values).forEach(function (k) {
          html +=
            "<tr><td>" +
            esc(k) +
            '</td><td class="num">' +
            num(d.missing_values[k]) +
            "</td></tr>";
        });
        html += "</tbody></table></div></div>";
      }

      appContent.innerHTML = html;
    });
  };

  // ---- EDA 可视化 ----
  pages.eda = function () {
    var types = [
      "response_distribution",
      "gender_response",
      "age_distribution",
      "premium_distribution",
    ];
    var labels = {
      response_distribution: "响应分布",
      gender_response: "性别 × 响应",
      age_distribution: "年龄分布",
      premium_distribution: "保费分布",
    };
    var html = head("EDA 可视化");
    html += '<div class="row">';
    types.forEach(function (t) {
      html +=
        '<div class="col-12 col-md-6 mb-3"><div class="card"><div class="card-body">';
      html += "<h6>" + esc(labels[t]) + "</h6>";
      html +=
        '<div class="chart-box" id="chart-' +
        t +
        '"><span class="text-muted small">加载中...</span></div>';
      html += "</div></div></div>";
    });
    html += "</div>";
    appContent.innerHTML = html;

    types.forEach(function (t) {
      api("GET", "/data/visualization/" + t).then(function (res) {
        var d = unwrap(res, true);
        var box = document.getElementById("chart-" + t);
        if (!box) return;
        if (d && d.image_base64) {
          box.innerHTML =
            '<img src="data:image/png;base64,' +
            esc(d.image_base64) +
            '" alt="' +
            esc(labels[t]) +
            '">';
        } else {
          box.innerHTML = '<span class="text-muted small">暂无数据</span>';
        }
      });
    });
  };

  // ---- 模型实验 ----
  pages.experiments = function () {
    loading("加载模型实验...");
    renderExperiments(1, "");
  };

  function renderExperiments(page, modelName) {
    var params = { page: page, per_page: 20 };
    if (modelName) params.model_name = modelName;
    api("GET", "/model/experiments" + qs(params)).then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var rows = d.items || [];
      var html = head(
        "模型实验",
        '<input class="form-control form-control-sm" id="exp-filter" placeholder="模型名称" style="width:140px" value="' +
          esc(modelName) +
          '">' +
          '<button class="btn btn-sm btn-outline-primary" id="exp-go">筛选</button>',
      );

      // best model summary
      api("GET", "/model/best").then(function (bres) {
        var bd = unwrap(bres, true);
        if (bd && bd.model_name) {
          html +=
            '<div class="card mb-3"><div class="card-body py-2"><small class="text-muted">当前最佳模型：</small><strong>' +
            esc(bd.model_name) +
            "</strong>";
          if (bd.roc_auc !== undefined)
            html += " · AUC = " + num(bd.roc_auc, 4);
          if (bd.accuracy !== undefined)
            html += " · Accuracy = " + num(bd.accuracy, 4);
          html += "</div></div>";
        }

        html +=
          '<div class="table-wrap"><table class="table table-hover"><thead><tr>' +
          '<th>ID</th><th>模型</th><th class="num">准确率</th><th class="num">精确率</th>' +
          '<th class="num">召回率</th><th class="num">F1</th><th class="num">ROC-AUC</th>' +
          "<th>最佳</th><th>创建时间</th></tr></thead><tbody>";

        if (!rows.length) {
          html += emptyRow(9, "暂无实验记录");
        } else {
          rows.forEach(function (r) {
            html +=
              "<tr>" +
              "<td>" +
              esc(r.id) +
              "</td>" +
              "<td>" +
              esc(r.model_name) +
              "</td>" +
              '<td class="num">' +
              num(r.accuracy, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.precision, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.recall, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.f1_score, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.roc_auc, 4) +
              "</td>" +
              "<td>" +
              (r.is_best ? '<span class="badge bg-warning">最佳</span>' : "-") +
              "</td>" +
              "<td>" +
              fmtDate(r.created_at) +
              "</td>" +
              "</tr>";
          });
        }
        html += "</tbody></table></div>";
        html += '<div id="exp-pager"></div>';
        appContent.innerHTML = html;

        mount(
          "#exp-pager",
          pager({ total: d.total, page: d.page, pages: d.pages }, function (p) {
            var fn = document.getElementById("exp-filter").value;
            renderExperiments(p, fn);
          }),
        );
        document
          .getElementById("exp-go")
          .addEventListener("click", function () {
            var fn = document.getElementById("exp-filter").value;
            renderExperiments(1, fn);
          });
      });
    });
  }

  // ---- 高潜客户 ----
  pages.targets = function () {
    loading("加载高潜客户...");
    renderTargets(1, "0.9");
  };

  function renderTargets(page, pctStr) {
    var params = { page: page, per_page: 20, percentile: pctStr || "0.9" };
    api("GET", "/email/targets" + qs(params)).then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var rows = d.customers || d.items || [];
      var html = head(
        "高潜客户筛选",
        '<select class="form-select form-select-sm" id="tgt-pct">' +
          '<option value="0.7">前 30%</option>' +
          '<option value="0.8">前 20%</option>' +
          '<option value="0.9" selected>前 10%</option>' +
          '<option value="0.95">前 5%</option>' +
          "</select>" +
          '<button class="btn btn-sm btn-outline-primary" id="tgt-go">筛选</button>',
      );

      if (d.threshold !== undefined) {
        html +=
          '<div class="alert alert-info py-2">筛选阈值：预测概率 ≥ <strong>' +
          fmtProb(d.threshold) +
          "</strong>，共 <strong>" +
          num(d.total) +
          "</strong> 位客户</div>";
      }

      html +=
        '<div class="table-wrap"><table class="table table-hover"><thead><tr>' +
        '<th>客户ID</th><th class="num">预测概率</th><th>性别</th><th class="num">年龄</th>' +
        '<th class="num">年保费</th><th>操作</th></tr></thead><tbody>';

      if (!rows.length) {
        html += emptyRow(6, "暂无高潜客户，请先训练模型并生成预测");
      } else {
        rows.forEach(function (c) {
          var gender =
            c.gender === 1 || c.gender === "Male"
              ? "男"
              : c.gender === 0 || c.gender === "Female"
                ? "女"
                : esc(c.gender);
          html +=
            "<tr>" +
            "<td>" +
            esc(c.id) +
            "</td>" +
            '<td class="num">' +
            fmtProb(c.predicted_prob) +
            "</td>" +
            "<td>" +
            esc(gender) +
            "</td>" +
            '<td class="num">' +
            num(c.age) +
            "</td>" +
            '<td class="num">' +
            num(c.annual_premium) +
            "</td>" +
            '<td><button class="btn btn-sm btn-primary" data-act="pick" data-id="' +
            esc(c.id) +
            '">选中</button></td>' +
            "</tr>";
        });
      }
      html += "</tbody></table></div>";
      html +=
        '<div class="d-flex gap-2 mt-2"><button class="btn btn-primary" id="btn-generate-all">生成全部高潜客户邮件</button></div>';
      html += '<div id="tgt-pager"></div>';

      appContent.innerHTML = html;

      mount(
        "#tgt-pager",
        pager(
          {
            total: d.total || rows.length,
            page: d.page || 1,
            pages: d.pages || 1,
          },
          function (p) {
            var pct = document.getElementById("tgt-pct").value;
            renderTargets(p, pct);
          },
        ),
      );
      document.getElementById("tgt-go").addEventListener("click", function () {
        var v = document.getElementById("tgt-pct").value;
        renderTargets(1, v);
      });
      document
        .getElementById("btn-generate-all")
        .addEventListener("click", function () {
          var v = document.getElementById("tgt-pct").value;
          var n = Math.ceil((1 - parseFloat(v)) * 1000);
          toast("正在为前 " + n + " 位客户生成邮件...", "info");
          api("POST", "/email/generate", { limit: n }).then(function (gres) {
            var gd = unwrap(gres);
            if (gd) {
              toast("已生成 " + num(gd.generated_count) + " 封邮件", "success");
              navigate("emails");
            }
          });
        });
    });
  }

  // ---- 邮件中心 ----
  pages.emails = function () {
    loading("加载邮件记录...");
    renderEmails(1, "");
  };

  function renderEmails(page, status) {
    var params = { page: page, per_page: 20 };
    if (status) params.status = status;
    api("GET", "/email/records" + qs(params)).then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var rows = d.items || [];
      var html = head(
        "邮件中心",
        '<select class="form-select form-select-sm" id="email-status">' +
          '<option value="">全部状态</option>' +
          '<option value="pending">待生成</option>' +
          '<option value="generated">已生成</option>' +
          '<option value="failed">失败</option>' +
          '<option value="sent">已发送</option>' +
          "</select>" +
          '<button class="btn btn-sm btn-outline-primary" id="email-go">筛选</button>' +
          '<button class="btn btn-sm btn-primary" id="btn-email-gen">批量生成</button>' +
          '<button class="btn btn-sm btn-danger" id="btn-email-del">批量删除</button>',
      );

      html +=
        '<div class="table-wrap"><table class="table table-hover"><thead><tr>' +
        '<th><input type="checkbox" id="chk-all"></th>' +
        "<th>ID</th><th>客户</th><th>主题</th><th>状态</th><th>创建时间</th><th>操作</th></tr></thead><tbody>";

      if (!rows.length) {
        html += emptyRow(7, "暂无邮件记录");
      } else {
        rows.forEach(function (r) {
          html +=
            "<tr>" +
            '<td><input type="checkbox" class="chk-email" data-id="' +
            esc(r.id) +
            '"></td>' +
            "<td>" +
            esc(r.id) +
            "</td>" +
            "<td>" +
            esc(r.customer_id || "") +
            "</td>" +
            "<td>" +
            esc(r.subject || "(无主题)") +
            "</td>" +
            "<td>" +
            statusBadge(r.status) +
            "</td>" +
            "<td>" +
            fmtDate(r.created_at) +
            "</td>" +
            '<td><button class="btn btn-sm btn-outline-primary" data-view="' +
            esc(r.id) +
            '">查看</button> ' +
            '<button class="btn btn-sm btn-outline-success" data-mark="' +
            esc(r.id) +
            '">标记已发送</button> ' +
            '<button class="btn btn-sm btn-outline-danger" data-del="' +
            esc(r.id) +
            '">删除</button></td>' +
            "</tr>";
        });
      }
      html += "</tbody></table></div>";
      html += '<div id="email-pager"></div>';
      html +=
        '<div class="modal fade" id="emailModal" tabindex="-1"><div class="modal-dialog modal-lg"><div class="modal-content"><div class="modal-header"><h5 class="modal-title">邮件详情</h5><button class="btn-close" data-bs-dismiss="modal"></button></div><div class="modal-body" id="email-modal-body"></div></div></div></div>';

      appContent.innerHTML = html;

      mount(
        "#email-pager",
        pager({ total: d.total, page: d.page, pages: d.pages }, function (p) {
          var s = document.getElementById("email-status").value;
          renderEmails(p, s);
        }),
      );

      document
        .getElementById("email-go")
        .addEventListener("click", function () {
          var s = document.getElementById("email-status").value;
          renderEmails(1, s);
        });

      document
        .getElementById("chk-all")
        .addEventListener("change", function (e) {
          document.querySelectorAll(".chk-email").forEach(function (c) {
            c.checked = e.target.checked;
          });
        });

      // row actions
      appContent.addEventListener("click", function (e) {
        var viewBtn = e.target.closest("[data-view]");
        var markBtn = e.target.closest("[data-mark]");
        var delBtn = e.target.closest("[data-del]");
        if (viewBtn) {
          var id = viewBtn.dataset.view;
          api("GET", "/email/records/" + id).then(function (r) {
            var dd = unwrap(r, true);
            if (!dd) return;
            document.getElementById("email-modal-body").innerHTML =
              (dd.subject ? "<h6>主题：" + esc(dd.subject) + "</h6>" : "") +
              '<div class="email-body">' +
              (dd.content || "") +
              "</div>" +
              '<p class="mt-2 small text-muted">状态：' +
              esc(dd.status) +
              " · " +
              fmtDate(dd.created_at) +
              "</p>";
            new bootstrap.Modal(document.getElementById("emailModal")).show();
          });
        } else if (markBtn) {
          var id2 = markBtn.dataset.mark;
          api("PATCH", "/email/records/" + id2, { status: "sent" }).then(
            function () {
              toast("已标记为已发送", "success");
              renderEmails(page, status);
            },
          );
        } else if (delBtn) {
          var id3 = delBtn.dataset.del;
          if (!confirm("确定删除此邮件记录？")) return;
          api("DELETE", "/email/records/" + id3).then(function () {
            toast("已删除", "success");
            renderEmails(page, status);
          });
        }
      });

      document
        .getElementById("btn-email-gen")
        .addEventListener("click", function () {
          toast("正在批量生成邮件...", "info");
          api("POST", "/email/generate", { limit: 20 }).then(function (r) {
            var dd = unwrap(r);
            if (dd) {
              toast(
                "生成完成：成功 " +
                  num(dd.generated_count) +
                  "，失败 " +
                  num(dd.failed_count),
                "success",
              );
              renderEmails(1, status);
            }
          });
        });

      document
        .getElementById("btn-email-del")
        .addEventListener("click", function () {
          var ids = [];
          document.querySelectorAll(".chk-email:checked").forEach(function (c) {
            ids.push(parseInt(c.dataset.id));
          });
          if (!ids.length) {
            toast("请先勾选要删除的记录", "warning");
            return;
          }
          if (!confirm("确定删除 " + ids.length + " 条记录？")) return;
          api("DELETE", "/email/records", { ids: ids }).then(function () {
            toast("批量删除完成", "success");
            renderEmails(page, status);
          });
        });
    });
  }

  // ---- 数据上传（admin only） ----
  pages.upload = function () {
    var html = head("数据上传");
    html += '<div class="card"><div class="card-body">';
    html += "<h6>上传 Excel 数据文件</h6>";
    html +=
      '<p class="text-muted small">支持 .xlsx / .xls 格式，单文件不超过 50MB。上传后将清空旧数据。</p>';
    html +=
      '<input type="file" class="form-control mb-2" id="file-input" accept=".xlsx,.xls">';
    html += '<button class="btn btn-primary" id="btn-upload">上传数据</button>';
    html += '<div id="upload-result" class="mt-3"></div>';
    html += "</div></div>";

    // quality info
    html += '<div class="card mt-3"><div class="card-body">';
    html +=
      '<h6>当前数据质量</h6><div id="upload-quality"><span class="text-muted small">加载中...</span></div>';
    html += "</div></div>";

    appContent.innerHTML = html;

    document
      .getElementById("btn-upload")
      .addEventListener("click", function () {
        var f = document.getElementById("file-input").files[0];
        if (!f) {
          toast("请选择文件", "warning");
          return;
        }
        var btn = document.getElementById("btn-upload");
        setBusy(btn, "上传中...");
        apiUpload("/data/upload", f).then(function (res) {
          clearBusy(btn);
          var d = unwrap(res);
          if (d) {
            toast("上传成功，导入 " + num(d.imported_count) + " 行", "success");
            var qr = d.quality_report || {};
            document.getElementById("upload-result").innerHTML =
              '<div class="alert alert-success">导入行数：<strong>' +
              num(d.imported_count) +
              "</strong></div>" +
              (qr
                ? '<div class="alert alert-info">质量报告：行数=' +
                  num(qr.total_rows) +
                  "，列数=" +
                  num(qr.total_cols) +
                  "，重复=" +
                  num(qr.duplicates) +
                  "</div>"
                : "");
            // refresh quality
            api("GET", "/data/quality").then(function (qr2) {
              var qd = unwrap(qr2, true);
              if (qd) renderUploadQuality(qd);
            });
          }
        });
      });

    api("GET", "/data/quality").then(function (r) {
      var qd = unwrap(r, true);
      if (qd) renderUploadQuality(qd);
      else
        document.getElementById("upload-quality").innerHTML =
          '<span class="text-muted small">暂无数据，请先上传</span>';
    });
  };

  function renderUploadQuality(d) {
    var html = '<table class="table table-sm"><tbody>';
    html +=
      '<tr><td>总行数</td><td class="num">' + num(d.total_rows) + "</td></tr>";
    html +=
      '<tr><td>列数</td><td class="num">' + num(d.total_cols) + "</td></tr>";
    html +=
      '<tr><td>重复行</td><td class="num">' + num(d.duplicates) + "</td></tr>";
    html += "</tbody></table>";
    document.getElementById("upload-quality").innerHTML = html;
  }

  // ---- 模型训练（admin only） ----
  pages.train = function () {
    var html = head("模型训练");
    html += '<div class="card"><div class="card-body">';
    html += "<h6>训练配置</h6>";
    html += '<div class="row g-2 align-items-end mb-2">';
    html +=
      '<div class="col-auto"><label class="form-label">测试集比例</label><input type="number" class="form-control" id="tr-test" value="0.2" step="0.05" min="0.1" max="0.5" style="width:100px"></div>';
    html +=
      '<div class="col-auto"><label class="form-label">随机种子</label><input type="number" class="form-control" id="tr-seed" value="42" style="width:90px"></div>';
    html += "</div>";
    html += '<div class="mb-2">';
    html += '<label class="form-label">算法选择</label>';
    html +=
      '<div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" id="m-lr" checked><label class="form-check-label">逻辑回归</label></div>';
    html +=
      '<div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" id="m-rf" checked><label class="form-check-label">随机森林</label></div>';
    html +=
      '<div class="form-check form-check-inline"><input class="form-check-input" type="checkbox" id="m-xgb" checked><label class="form-check-label">XGBoost</label></div>';
    html += "</div>";
    html += '<button class="btn btn-primary" id="btn-train">开始训练</button>';
    html += '<div id="train-result" class="mt-3"></div>';
    html += "</div></div>";
    appContent.innerHTML = html;

    document.getElementById("btn-train").addEventListener("click", function () {
      var btn = document.getElementById("btn-train");
      setBusy(btn, "训练中...");
      var models = [];
      if (document.getElementById("m-lr").checked)
        models.push("logistic_regression");
      if (document.getElementById("m-rf").checked) models.push("random_forest");
      if (document.getElementById("m-xgb").checked) models.push("xgboost");
      if (!models.length) {
        clearBusy(btn);
        toast("请至少选择一个算法", "warning");
        return;
      }
      var body = {
        models: models,
        test_size: parseFloat(document.getElementById("tr-test").value),
        random_state: parseInt(document.getElementById("tr-seed").value),
      };
      api("POST", "/model/train", body).then(function (res) {
        clearBusy(btn);
        var d = unwrap(res);
        if (d) {
          var h =
            '<div class="alert alert-success">训练完成！最佳模型：<strong>' +
            esc(d.best_model) +
            "</strong></div>";
          h +=
            '<table class="table table-sm mt-2"><thead><tr><th>模型</th><th class="num">准确率</th><th class="num">精确率</th><th class="num">召回率</th><th class="num">F1</th><th class="num">AUC</th></tr></thead><tbody>';
          Object.keys(d.results || {}).forEach(function (m) {
            var r = d.results[m];
            h +=
              "<tr><td>" +
              esc(m) +
              "</td>" +
              '<td class="num">' +
              num(r.accuracy, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.precision, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.recall, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.f1_score, 4) +
              "</td>" +
              '<td class="num">' +
              num(r.roc_auc, 4) +
              "</td></tr>";
          });
          h += "</tbody></table>";
          document.getElementById("train-result").innerHTML = h;
          toast("训练完成：" + esc(d.best_model), "success");
        }
      });
    });
  };

  // ---- 模型管理（admin only） ----
  pages.modelmgmt = function () {
    var html = head("模型管理");
    html += '<div class="row"><div class="col-12 col-md-6 mb-3">';
    html += '<div class="card"><div class="card-body">';
    html += "<h6>全量预测</h6>";
    html +=
      '<p class="text-muted small">使用最佳模型对所有客户进行预测，回写预测概率字段。</p>';
    html +=
      '<button class="btn btn-primary" id="btn-predict">执行全量预测</button>';
    html += '<div id="predict-result" class="mt-2"></div>';
    html += "</div></div></div>";
    html += '<div class="col-12 col-md-6 mb-3">';
    html += '<div class="card"><div class="card-body">';
    html += "<h6>导出/导入模型</h6>";
    html +=
      '<div class="mb-2"><label class="form-label">导出模型</label><select class="form-select form-select-sm" id="export-name"><option value="">-- 选择模型 --</option></select><button class="btn btn-sm btn-outline-primary mt-1" id="btn-export">导出</button></div>';
    html +=
      '<div><label class="form-label">导入 .joblib 文件</label><input type="file" class="form-control form-control-sm" id="import-file" accept=".joblib"><button class="btn btn-sm btn-outline-primary mt-1" id="btn-import">导入</button></div>';
    html += "</div></div></div></div>";

    html += '<div class="card"><div class="card-body">';
    html += "<h6>模型评估可视化</h6>";
    html += '<div class="row g-2 mb-2 align-items-end">';
    html +=
      '<div class="col-auto"><label class="form-label">图表类型</label><select class="form-select form-select-sm" id="viz-type"><option value="roc_curve">ROC 曲线</option><option value="metrics_comparison">指标对比</option><option value="confusion_matrix">混淆矩阵</option><option value="feature_importance">特征重要性</option></select></div>';
    html +=
      '<div class="col-auto"><label class="form-label">模型</label><select class="form-select form-select-sm" id="viz-model"><option value="">最佳模型</option></select></div>';
    html +=
      '<div class="col-auto"><button class="btn btn-sm btn-primary" id="btn-viz">生成</button></div>';
    html += "</div>";
    html +=
      '<div class="chart-box" id="viz-chart"><span class="text-muted small">选择图表类型后点击生成</span></div>';
    html += "</div></div>";

    appContent.innerHTML = html;

    // populate model selectors
    api("GET", "/model/experiments?page=1&per_page=50").then(function (res) {
      var d = unwrap(res, true);
      if (!d) return;
      var models = {};
      (d.items || []).forEach(function (e) {
        models[e.model_name] = 1;
      });
      Object.keys(models).forEach(function (m) {
        document.getElementById("export-name").innerHTML +=
          '<option value="' + esc(m) + '">' + esc(m) + "</option>";
        document.getElementById("viz-model").innerHTML +=
          '<option value="' + esc(m) + '">' + esc(m) + "</option>";
      });
    });

    // predict
    document
      .getElementById("btn-predict")
      .addEventListener("click", function () {
        toast("正在执行全量预测...", "info");
        api("POST", "/model/predict", {}).then(function (res) {
          var d = unwrap(res);
          if (d) {
            document.getElementById("predict-result").innerHTML =
              '<div class="alert alert-success">预测完成！模型：<strong>' +
              esc(d.model_name) +
              "</strong>，共预测 " +
              num(d.predicted_count) +
              " 位客户</div>";
            toast("全量预测完成", "success");
          }
        });
      });

    // export
    document
      .getElementById("btn-export")
      .addEventListener("click", function () {
        var name = document.getElementById("export-name").value;
        if (!name) {
          toast("请先选择模型", "warning");
          return;
        }
        var r = apiDownload(
          "/model/export/" + encodeURIComponent(name),
          name + ".joblib",
        );
        toast("已触发下载：" + esc(name) + ".joblib", "info");
      });

    // import
    document
      .getElementById("btn-import")
      .addEventListener("click", function () {
        var f = document.getElementById("import-file").files[0];
        if (!f) {
          toast("请先选择文件", "warning");
          return;
        }
        apiUpload("/model/import", f).then(function (res) {
          var d = unwrap(res);
          if (d) toast("模型导入成功", "success");
        });
      });

    // viz
    document.getElementById("btn-viz").addEventListener("click", function () {
      var t = document.getElementById("viz-type").value;
      var m = document.getElementById("viz-model").value;
      var p = {};
      if (m) p.model = m;
      var box = document.getElementById("viz-chart");
      box.innerHTML = '<span class="text-muted small">加载中...</span>';
      api("GET", "/model/visualization/" + t + qs(p)).then(function (res) {
        var d = unwrap(res, true);
        if (d && d.image_base64) {
          box.innerHTML =
            '<img src="data:image/png;base64,' + esc(d.image_base64) + '">';
        } else {
          box.innerHTML =
            '<span class="text-muted small">暂无数据，请先训练模型</span>';
        }
      });
    });
  };

  // ---- 操作日志（admin only） ----
  pages.logs = function () {
    loading("加载操作日志...");
    renderLogs(1, "", "");
  };

  function renderLogs(page, userId, action) {
    var params = { page: page, per_page: 20 };
    if (userId) params.user_id = userId;
    if (action) params.action = action;
    api("GET", "/logs" + qs(params)).then(function (res) {
      var d = unwrap(res);
      if (!d) return;
      var rows = d.items || [];
      var html = head(
        "操作日志",
        '<input class="form-control form-control-sm" id="log-user" placeholder="用户ID" style="width:100px" value="' +
          esc(userId) +
          '">' +
          '<select class="form-select form-select-sm" id="log-action"><option value="">全部操作</option>' +
          '<option value="model_training">训练</option>' +
          '<option value="prediction">预测</option>' +
          '<option value="model_import">导入模型</option>' +
          '<option value="email_generation">邮件生成</option>' +
          '<option value="email_update">邮件更新</option>' +
          '<option value="email_delete">邮件删除</option>' +
          "</select>" +
          '<button class="btn btn-sm btn-outline-primary" id="log-go">筛选</button>',
      );

      html +=
        '<div class="table-wrap"><table class="table table-hover"><thead><tr>' +
        "<th>ID</th><th>用户</th><th>操作</th><th>详情</th><th>时间</th></tr></thead><tbody>";

      if (!rows.length) {
        html += emptyRow(5, "暂无日志");
      } else {
        rows.forEach(function (r) {
          html +=
            "<tr>" +
            "<td>" +
            esc(r.id) +
            "</td>" +
            "<td>" +
            esc(r.username || r.user_id || "-") +
            "</td>" +
            '<td><span class="badge bg-primary">' +
            esc(r.action) +
            "</span></td>" +
            '<td class="mono">' +
            esc(r.details ? JSON.stringify(r.details).substring(0, 100) : "") +
            "</td>" +
            "<td>" +
            fmtDate(r.created_at) +
            "</td>" +
            "</tr>";
        });
      }
      html += "</tbody></table></div>";
      html += '<div id="log-pager"></div>';
      appContent.innerHTML = html;

      mount(
        "#log-pager",
        pager({ total: d.total, page: d.page, pages: d.pages }, function (p) {
          var u = document.getElementById("log-user").value;
          var a = document.getElementById("log-action").value;
          renderLogs(p, u, a);
        }),
      );
      document.getElementById("log-go").addEventListener("click", function () {
        var u = document.getElementById("log-user").value;
        var a = document.getElementById("log-action").value;
        renderLogs(1, u, a);
      });
    });
  }

  // ============ 认证 ============

  function showLogin() {
    loginPage.classList.remove("d-none");
    registerPage.classList.add("d-none");
    appPage.classList.add("d-none");
    document.getElementById("login-error").classList.add("d-none");
  }

  function showRegister() {
    loginPage.classList.add("d-none");
    registerPage.classList.remove("d-none");
    appPage.classList.add("d-none");
    document.getElementById("register-error").classList.add("d-none");
    document.getElementById("register-success").classList.add("d-none");
  }

  function showApp() {
    loginPage.classList.add("d-none");
    registerPage.classList.add("d-none");
    appPage.classList.remove("d-none");
    currentUserEl.textContent =
      (currentUser && currentUser.username) + (isAdmin() ? " (admin)" : "");
    buildMenus();
    route();
  }

  function handleLogin() {
    var username = document.getElementById("username").value.trim();
    var password = document.getElementById("password").value;
    if (!username || !password) return;
    var errEl = document.getElementById("login-error");
    errEl.classList.add("d-none");
    api("POST", "/auth/login", { username: username, password: password }).then(
      function (res) {
        if (res.code === 0) {
          setToken(res.data.access_token);
          setCachedUser(res.data.user);
          currentUser = res.data.user;
          showApp();
        } else {
          errEl.textContent = res.message || "登录失败";
          errEl.classList.remove("d-none");
        }
      },
    );
  }

  function handleRegister() {
    var username = document.getElementById("reg-username").value.trim();
    var password = document.getElementById("reg-password").value;
    if (!username || !password) return;
    var errEl = document.getElementById("register-error");
    var okEl = document.getElementById("register-success");
    errEl.classList.add("d-none");
    okEl.classList.add("d-none");
    api("POST", "/auth/register", {
      username: username,
      password: password,
    }).then(function (res) {
      if (res.code === 0) {
        okEl.textContent = "注册成功！请登录。";
        okEl.classList.remove("d-none");
        document.getElementById("reg-username").value = "";
        document.getElementById("reg-password").value = "";
      } else {
        errEl.textContent = res.message || "注册失败";
        errEl.classList.remove("d-none");
      }
    });
  }

  function logout() {
    api("POST", "/auth/logout", {}).then(function () {
      clearToken();
      clearCachedUser();
      currentUser = null;
      location.hash = "";
      showLogin();
      toast("已退出登录", "info");
    });
  }

  function checkAuth() {
    var token = getToken();
    if (!token) {
      showLogin();
      return;
    }
    api("GET", "/auth/me").then(function (res) {
      if (res.code === 0) {
        currentUser = res.data;
        setCachedUser(currentUser);
        showApp();
      } else if (res.code === 1002) {
        clearToken();
        clearCachedUser();
        currentUser = null;
        showLogin();
      }
    });
  }

  // ============ 启动 ============

  setUnauthorizedHandler(function () {
    currentUser = null;
    location.hash = "";
    showLogin();
    toast("登录已过期，请重新登录", "warning");
  });

  document
    .getElementById("login-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      handleLogin();
    });
  document
    .getElementById("register-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      handleRegister();
    });
  document
    .getElementById("show-register")
    .addEventListener("click", function (e) {
      e.preventDefault();
      showRegister();
    });
  document.getElementById("show-login").addEventListener("click", function (e) {
    e.preventDefault();
    showLogin();
  });
  document.getElementById("btn-logout").addEventListener("click", logout);

  window.addEventListener("hashchange", route);

  // 全局错误捕获
  window.addEventListener("error", function (e) {
    console.error("全局错误:", e.error || e.message);
  });
  window.addEventListener("unhandledrejection", function (e) {
    console.error("未处理的 Promise 异常:", e.reason);
  });

  // 初始加载
  checkAuth();
})();
