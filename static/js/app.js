let currentCategory = "ALL";
let searchTimer = null;

const $ = (id) =>
    document.getElementById(id);


async function fetchJSON(url, options = {}) {

    const response = await fetch(
        url,
        {
            cache: "no-store",
            ...options,
        }
    );

    if (!response.ok) {
        throw new Error(
            `${response.status} ${response.statusText}`
        );
    }

    return response.json();
}


function setStatus(
    message,
    healthy = true
) {

    const status = $("status");
    const dot = $("status-dot");

    if (status) {
        status.textContent = message;
    }

    if (dot) {
        dot.style.background =
            healthy
                ? "var(--green)"
                : "var(--danger)";
    }
}


function formatDate(value) {

    if (!value) {
        return "Unknown time";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "Unknown time";
    }

    return date.toLocaleString(
        undefined,
        {
            dateStyle: "medium",
            timeStyle: "short",
        }
    );
}


function escapeHTML(value) {

    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


async function loadStats() {

    try {

        const data =
            await fetchJSON(
                "/api/stats"
            );

        $("source-count").textContent =
            data.sources ?? 0;

        $("article-count").textContent =
            data.articles ?? 0;

    }
    catch (error) {

        console.error(
            "Stats error:",
            error
        );
    }
}


async function loadIntelligence() {

    const container =
        $("intelligence-feed");

    if (!container) {
        return;
    }

    try {

        const data =
            await fetchJSON(
                "/api/intelligence"
            );

        $("event-count").textContent =
            data.event_clusters ?? 0;

        $("multi-source-count").textContent =
            data.multi_source_events ?? 0;

        const events =
            await fetchJSON(
                "/api/events?multi_source=true&limit=12"
            );

        if (!events.length) {

            container.innerHTML =
                '<div class="empty-state">No multi-source developments detected yet.</div>';

            return;
        }

        container.innerHTML =
            events.map(
                (event) => {

                    const sources =
                        (event.sources || [])
                            .map(
                                escapeHTML
                            )
                            .join(", ");

                    return `
                        <article class="intelligence-card">

                            <div class="intelligence-top">

                                <span class="intelligence-category">
                                    ${escapeHTML(event.category)}
                                </span>

                                <span class="relevance">
                                    ${event.relevance ?? 0}
                                </span>

                            </div>

                            <h3>
                                ${escapeHTML(event.title)}
                            </h3>

                            <div class="intelligence-meta">

                                <span>
                                    ${event.article_count ?? 0}
                                    articles
                                </span>

                                <span>
                                    ${event.source_count ?? 0}
                                    sources
                                </span>

                                <span>
                                    similarity
                                    ${event.similarity ?? 0}
                                </span>

                                <span>
                                    ${sources}
                                </span>

                            </div>

                        </article>
                    `;
                }
            )
            .join("");

    }
    catch (error) {

        console.error(
            "Intelligence error:",
            error
        );

        container.innerHTML =
            '<div class="empty-state">Intelligence feed temporarily unavailable.</div>';
    }
}


async function loadNews() {

    const container =
        $("news-feed");

    if (!container) {
        return;
    }

    container.innerHTML =
        '<div class="empty-state">Loading articles...</div>';

    try {

        const params =
            new URLSearchParams();

        params.set(
            "limit",
            "100"
        );

        if (
            currentCategory
            && currentCategory !== "ALL"
        ) {
            params.set(
                "category",
                currentCategory
            );
        }

        const search =
            $("search-input")?.value.trim();

        if (search) {
            params.set(
                "search",
                search
            );
        }

        const articles =
            await fetchJSON(
                `/api/news?${params.toString()}`
            );

        $("story-count").textContent =
            `${articles.length} stories`;

        if (!articles.length) {

            container.innerHTML =
                '<div class="empty-state">No articles found.</div>';

            return;
        }

        container.innerHTML =
            articles.map(
                (article) => {

                    const summary =
                        article.summary
                        || "No summary available.";

                    return `
                        <article class="article-card">

                            <div class="article-category">
                                ${escapeHTML(article.category)}
                            </div>

                            <h3>
                                <a
                                    href="${escapeHTML(article.url)}"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    ${escapeHTML(article.title)}
                                </a>
                            </h3>

                            <div class="article-summary">
                                ${escapeHTML(
                                    summary.slice(0, 280)
                                )}
                            </div>

                            <div class="article-meta">

                                <span>
                                    ${escapeHTML(article.source)}
                                </span>

                                <span>
                                    ${formatDate(
                                        article.published_at
                                    )}
                                </span>

                            </div>

                        </article>
                    `;
                }
            )
            .join("");

    }
    catch (error) {

        console.error(
            "News error:",
            error
        );

        $("story-count").textContent =
            "0 stories";

        container.innerHTML =
            '<div class="empty-state">Unable to load articles.</div>';
    }
}


async function loadCategories() {

    const container =
        $("category-filters");

    if (!container) {
        return;
    }

    try {

        const data =
            await fetchJSON(
                "/api/stats"
            );

        const categories =
            Object.keys(
                data.categories || {}
            ).sort();

        const allCategories =
            ["ALL", ...categories];

        container.innerHTML =
            allCategories.map(
                (category) => `
                    <button
                        class="category-button ${
                            category === currentCategory
                                ? "active"
                                : ""
                        }"
                        data-category="${escapeHTML(category)}"
                    >
                        ${escapeHTML(category)}
                    </button>
                `
            ).join("");

        container
            .querySelectorAll(
                ".category-button"
            )
            .forEach(
                (button) => {

                    button.addEventListener(
                        "click",
                        () => {

                            currentCategory =
                                button.dataset.category;

                            container
                                .querySelectorAll(
                                    ".category-button"
                                )
                                .forEach(
                                    (item) =>
                                        item.classList.remove(
                                            "active"
                                        )
                                );

                            button.classList.add(
                                "active"
                            );

                            loadNews();
                        }
                    );
                }
            );

    }
    catch (error) {

        console.error(
            "Category error:",
            error
        );
    }
}


async function refreshDashboard() {

    setStatus(
        "REFRESHING",
        true
    );

    await Promise.all([
        loadStats(),
        loadCategories(),
        loadNews(),
        loadIntelligence(),
    ]);

    setStatus(
        "LIVE",
        true
    );
}


async function collectNews() {

    const button =
        $("collect-button");

    if (button) {
        button.disabled = true;
        button.textContent =
            "COLLECTING...";
    }

    setStatus(
        "COLLECTING",
        true
    );

    try {

        const result =
            await fetchJSON(
                "/api/collect",
                {
                    method: "POST",
                }
            );

        console.log(
            "Collection result:",
            result
        );

        await refreshDashboard();

    }
    catch (error) {

        console.error(
            "Collection error:",
            error
        );

        setStatus(
            "COLLECTION ERROR",
            false
        );

    }
    finally {

        if (button) {
            button.disabled = false;
            button.textContent =
                "COLLECT NEWS";
        }
    }
}


function initialize() {

    const refresh =
        $("refresh-button");

    if (refresh) {

        refresh.addEventListener(
            "click",
            refreshDashboard
        );
    }

    const collect =
        $("collect-button");

    if (collect) {

        collect.addEventListener(
            "click",
            collectNews
        );
    }

    const search =
        $("search-input");

    if (search) {

        search.addEventListener(
            "input",
            () => {

                clearTimeout(
                    searchTimer
                );

                searchTimer =
                    setTimeout(
                        loadNews,
                        300
                    );
            }
        );
    }

    refreshDashboard();
}


document.addEventListener(
    "DOMContentLoaded",
    initialize
);
