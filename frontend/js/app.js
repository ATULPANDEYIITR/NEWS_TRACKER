const API_BASE = "";

const elements = {
    apiStatus: document.getElementById("apiStatus"),

    totalArticles: document.getElementById("totalArticles"),
    totalSources: document.getElementById("totalSources"),
    activeSources: document.getElementById("activeSources"),
    totalCategories: document.getElementById("totalCategories"),
    articlesToday: document.getElementById("articlesToday"),
    articles24h: document.getElementById("articles24h"),

    articlesContainer:
        document.getElementById("articlesContainer"),

    categoriesContainer:
        document.getElementById("categoriesContainer"),

    sourcesContainer:
        document.getElementById("sourcesContainer"),

    oneLineContainer:
        document.getElementById("oneLineContainer"),

    categoryExplorer:
        document.getElementById("categoryExplorer"),

    categoryArticles:
        document.getElementById("categoryArticles"),

    searchInput:
        document.getElementById("searchInput"),

    searchButton:
        document.getElementById("searchButton"),

    refreshButton:
        document.getElementById("refreshButton"),

    latestButton:
        document.getElementById("latestButton")
};


function formatNumber(value) {

    return new Intl.NumberFormat("en-IN")
        .format(value || 0);

}


function formatDate(value) {

    if (!value) {
        return "Unknown time";
    }

    try {

        return new Date(value)
            .toLocaleString(
                "en-IN",
                {
                    dateStyle: "medium",
                    timeStyle: "short"
                }
            );

    } catch {

        return value;

    }

}


function escapeHTML(value) {

    if (value === null || value === undefined) {
        return "";
    }

    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


async function fetchJSON(url) {

    const response = await fetch(
        API_BASE + url,
        {
            headers: {
                "Accept": "application/json"
            }
        }
    );

    if (!response.ok) {

        throw new Error(
            `HTTP ${response.status}`
        );

    }

    return response.json();

}


function renderArticle(article) {

    return `
        <article class="article">

            <div class="article-source">
                ${escapeHTML(article.source?.name || article.source || "Unknown Source")}
            </div>

            <h4>
                <a
                    href="${escapeHTML(article.original_url || "#")}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    ${escapeHTML(article.headline)}
                </a>
            </h4>

            ${
                article.description
                    ? `
                    <p class="article-description">
                        ${escapeHTML(article.description)}
                    </p>
                    `
                    : ""
            }

            <div class="article-meta">

                <span>
                    ${escapeHTML(article.country || "Global")}
                </span>

                <span>
                    ${escapeHTML(article.region || "")}
                </span>

                <span>
                    ${formatDate(article.published_at)}
                </span>

            </div>

        </article>
    `;

}


async function loadDashboard() {

    try {

        elements.apiStatus.textContent =
            "● Connecting";

        const data =
            await fetchJSON(
                "/api/dashboard/overview"
            );

        elements.totalArticles.textContent =
            formatNumber(data.totals.articles);

        elements.totalSources.textContent =
            formatNumber(data.totals.sources);

        elements.activeSources.textContent =
            formatNumber(data.totals.active_sources);

        elements.totalCategories.textContent =
            formatNumber(data.totals.categories);

        elements.articlesToday.textContent =
            formatNumber(data.totals.articles_today);

        elements.articles24h.textContent =
            formatNumber(data.totals.articles_last_24_hours);


        renderCategories(
            data.top_categories || []
        );

        renderSources(
            data.top_sources || []
        );


        elements.apiStatus.textContent =
            "● API Online";

    } catch (error) {

        console.error(error);

        elements.apiStatus.textContent =
            "● API Error";

    }

}


async function loadArticles() {

    elements.articlesContainer.innerHTML =
        `<div class="loading">Loading news...</div>`;

    try {

        const data =
            await fetchJSON(
                "/api/articles?page=1&page_size=20"
            );

        if (!data.articles.length) {

            elements.articlesContainer.innerHTML =
                `<div class="loading">No articles found.</div>`;

            return;
        }

        elements.articlesContainer.innerHTML =
            data.articles
                .map(renderArticle)
                .join("");

    } catch (error) {

        console.error(error);

        elements.articlesContainer.innerHTML =
            `<div class="error">
                Unable to load articles.
            </div>`;

    }

}


function renderCategories(categories) {

    elements.categoriesContainer.innerHTML =
        categories
            .map(
                category => `
                    <div class="category-row">

                        <span class="category-name">
                            ${escapeHTML(category.name)}
                        </span>

                        <span class="category-count">
                            ${formatNumber(category.article_count)}
                        </span>

                    </div>
                `
            )
            .join("");

    elements.categoryExplorer.innerHTML =
        categories
            .map(
                category => `
                    <button
                        class="category-button"
                        data-category="${escapeHTML(category.name)}"
                    >
                        ${escapeHTML(category.name)}
                    </button>
                `
            )
            .join("");

    document
        .querySelectorAll(".category-button")
        .forEach(button => {

            button.addEventListener(
                "click",
                () => {

                    loadCategory(
                        button.dataset.category
                    );

                }
            );

        });

}


function renderSources(sources) {

    elements.sourcesContainer.innerHTML =
        sources
            .map(
                source => `
                    <div class="source-row">

                        <span class="source-name">
                            ${escapeHTML(source.name)}
                        </span>

                        <span class="source-count">
                            ${formatNumber(source.article_count)}
                        </span>

                    </div>
                `
            )
            .join("");

}


async function loadOneLineNews() {

    elements.oneLineContainer.innerHTML =
        `<div class="loading">
            Loading briefings...
        </div>`;

    try {

        const data =
            await fetchJSON(
                "/api/one-line-news?limit=20"
            );

        if (!data.length) {

            elements.oneLineContainer.innerHTML =
                `<div class="loading">
                    No briefings available.
                </div>`;

            return;
        }

        elements.oneLineContainer.innerHTML =
            data
                .map(
                    item => `
                        <div class="one-line-item">

                            <div class="one-line-source">
                                ${escapeHTML(item.source)}
                            </div>

                            <div class="one-line-text">

                                <a
                                    href="${escapeHTML(item.original_url || "#")}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    style="color:inherit;text-decoration:none;"
                                >
                                    ${escapeHTML(item.one_line)}
                                </a>

                            </div>

                        </div>
                    `
                )
                .join("");

    } catch (error) {

        console.error(error);

        elements.oneLineContainer.innerHTML =
            `<div class="error">
                Unable to load one-line news.
            </div>`;

    }

}


async function searchNews() {

    const query =
        elements.searchInput.value.trim();

    if (!query) {

        await loadArticles();

        return;
    }

    elements.articlesContainer.innerHTML =
        `<div class="loading">
            Searching...
        </div>`;

    try {

        const data =
            await fetchJSON(
                `/api/search?q=${encodeURIComponent(query)}&limit=50`
            );

        if (!data.results.length) {

            elements.articlesContainer.innerHTML =
                `<div class="loading">
                    No results found for
                    "${escapeHTML(query)}".
                </div>`;

            return;
        }

        elements.articlesContainer.innerHTML =
            data.results
                .map(renderArticle)
                .join("");

    } catch (error) {

        console.error(error);

        elements.articlesContainer.innerHTML =
            `<div class="error">
                Search failed.
            </div>`;

    }

}


async function loadCategory(categoryName) {

    elements.categoryArticles.innerHTML =
        `<div class="loading">
            Loading ${escapeHTML(categoryName)} news...
        </div>`;

    try {

        const data =
            await fetchJSON(
                `/api/dashboard/category/${encodeURIComponent(categoryName)}`
            );

        if (!data.articles.length) {

            elements.categoryArticles.innerHTML =
                `<div class="loading">
                    No articles found.
                </div>`;

            return;
        }

        elements.categoryArticles.innerHTML =
            data.articles
                .slice(0, 30)
                .map(renderArticle)
                .join("");

        elements.categoryArticles.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });

    } catch (error) {

        console.error(error);

        elements.categoryArticles.innerHTML =
            `<div class="error">
                Unable to load category.
            </div>`;

    }

}


async function refreshAll() {

    elements.refreshButton.textContent =
        "Refreshing...";

    await Promise.all([
        loadDashboard(),
        loadArticles(),
        loadOneLineNews()
    ]);

    elements.refreshButton.textContent =
        "Refresh";

}


elements.searchButton.addEventListener(
    "click",
    searchNews
);


elements.searchInput.addEventListener(
    "keydown",
    event => {

        if (event.key === "Enter") {
            searchNews();
        }

    }
);


elements.refreshButton.addEventListener(
    "click",
    refreshAll
);


elements.latestButton.addEventListener(
    "click",
    loadArticles
);


refreshAll();

/* GLOBAL_NEWS_TRACKER_AUTO_REFRESH
   Refresh dashboard data automatically.
   The backend remains the source of truth.
*/
(function () {
    const AUTO_REFRESH_INTERVAL = 60 * 1000;

    setInterval(function () {
        if (document.visibilityState === "visible") {
            window.location.reload();
        }
    }, AUTO_REFRESH_INTERVAL);
})();
