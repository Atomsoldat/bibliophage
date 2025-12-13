"""
Batch Size Calculator for Docling PDF Processing

Calculates optimal batch size based on available system memory and PDF characteristics.

Based on empirical data:
- Pathfinder 1E Core Rulebook (table-heavy): ~67.8 MB per page
- Models + overhead: ~500 MB baseline
"""

import psutil


def get_available_memory_gb() -> float:
    """
    Get available system memory in GB.

    Returns the amount of memory that can safely be used without
    causing the system to swap.
    """
    mem: psutil.svmem = psutil.virtual_memory()
    # Use available memory (not total) to account for OS and other processes
    # Leave 1GB for system operations
    available_gb: float = (mem.available / (1024**3)) - 1.0
    return max(available_gb, 0.5)  # At least 500MB


# TODO: We probably want  these to be configurable
def calculate_batch_size(
    available_ram_gb: float = None,
    memory_per_page_mb: float = 67.8,
    overhead_gb: float = 0.5,
    safety_margin: float = 0.8,
    min_batch_size: int = 1,
    max_batch_size: int = 500
) -> dict:
    """
    Calculate optimal batch size for Docling PDF processing.

    Args:
        available_ram_gb: Available RAM in GB. If None, auto-detect from system.
        memory_per_page_mb: Estimated memory usage per page in MB.
                           Defaults to 67.8 MB (table-heavy PDFs like Pathfinder Core).
                           Use lower values (30-50 MB) for text-heavy PDFs,
                           higher values (80-150 MB) for image-heavy PDFs.
        overhead_gb: Baseline overhead in GB (models, Python, etc.). Default: 0.5 GB
        safety_margin: Safety factor (0.0-1.0). Default: 0.8 (use 80% of calculated max)
        min_batch_size: Minimum batch size. Default: 1 page
        max_batch_size: Maximum batch size. Default: 500 pages

    Returns:
        dict with:
            - recommended_batch_size: Recommended batch size in pages
            - peak_memory_gb: Expected peak memory usage in GB
            - available_ram_gb: Available RAM in GB
            - memory_per_page_mb: Memory per page used in calculation
    """
    # Auto-detect available RAM if not provided
    if available_ram_gb is None:
        available_ram_gb = get_available_memory_gb()

    # Calculate usable memory (after overhead)
    usable_gb: float = available_ram_gb - overhead_gb

    if usable_gb <= 0:
        raise ValueError(
            f"Insufficient RAM: {available_ram_gb:.1f}GB available, "
            f"but {overhead_gb:.1f}GB needed for overhead. "
        )

    # Convert to MB for calculation
    usable_mb: float = usable_gb * 1024

    # Calculate theoretical max pages
    theoretical_max_pages: float = usable_mb / memory_per_page_mb

    # Apply safety margin
    safe_max_pages: float = theoretical_max_pages * safety_margin

    # Clamp to [min_batch_size, max_batch_size]
    safe_max_batch_size = int(safe_max_pages)
    recommended_batch_size: int = max( min( max_batch_size, safe_max_batch_size), min_batch_size )

    # Calculate expected peak memory
    peak_memory_gb: float = overhead_gb + (recommended_batch_size * memory_per_page_mb / 1024)

    return {
        'recommended_batch_size': recommended_batch_size,
        'peak_memory_gb': round(peak_memory_gb, 2),
        'available_ram_gb': round(available_ram_gb, 2),
        'memory_per_page_mb': memory_per_page_mb,
        'usable_ram_gb': round(usable_gb, 2),
        'safety_margin': safety_margin,
    }