from __future__ import annotations

import asyncio
import inspect
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.logging import setup_logging

setup_logging()

logger = logging.getLogger("live_news_collection")


def find_callable(module, candidates):
    for name in candidates:
        obj = getattr(module, name, None)
        if callable(obj):
            return obj
    return None


def execute_callable(func):
    result = func()

    if inspect.isawaitable(result):
        return asyncio.run(result)

    return result


def run_collection():
    logger.info("Starting live news collection")

    import app.collectors.rss_collector as collector

    collector_function = find_callable(
        collector,
        [
            "collect_all_sources",
            "collect_all_feeds",
            "collect_news",
            "collect_feeds",
            "run_collection",
            "collect",
            "run",
        ],
    )

    if collector_function is None:
        logger.warning(
            "No collection function found by name. "
            "Trying module execution."
        )

        import runpy

        runpy.run_module(
            "app.collectors.rss_collector",
            run_name="__main__",
        )

    else:
        logger.info(
            "Using collector function: %s",
            collector_function.__name__,
        )

        execute_callable(collector_function)

    logger.info("News collection completed")


def run_intelligence():
    logger.info("Starting news intelligence engine")

    try:
        from app.analytics.intelligence_engine import run_intelligence

        run_intelligence()

        logger.info(
            "News intelligence engine completed"
        )

    except Exception:
        logger.exception(
            "News intelligence engine failed"
        )


def run_processing():
    logger.info("Starting article intelligence processing")

    possible_modules = [
        "app.processors.news_processor",
        "app.processors.processor",
    ]

    possible_functions = [
        "process_all_articles",
        "process_articles",
        "process_news",
        "run_processing",
        "run_processor",
        "process_all",
        "process",
    ]

    for module_name in possible_modules:
        try:
            module = __import__(
                module_name,
                fromlist=["*"],
            )

            processor_function = find_callable(
                module,
                possible_functions,
            )

            if processor_function is not None:
                logger.info(
                    "Using processor function: %s.%s",
                    module_name,
                    processor_function.__name__,
                )

                execute_callable(processor_function)
                logger.info("Article processing completed")
                return

        except ModuleNotFoundError:
            continue

        except Exception:
            logger.exception(
                "Processor failed in module %s",
                module_name,
            )
            return

    logger.info(
        "No standalone processor entry point found. "
        "Existing processing pipeline was left unchanged."
    )


def main():
    try:
        run_collection()
        run_processing()
        run_intelligence()

        logger.info(
            "=========================================="
        )
        logger.info(
            "LIVE NEWS UPDATE COMPLETED SUCCESSFULLY"
        )
        logger.info(
            "=========================================="
        )

    except Exception:
        logger.exception(
            "LIVE NEWS UPDATE FAILED"
        )
        raise


if __name__ == "__main__":
    main()

