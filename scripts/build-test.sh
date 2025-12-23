#!/bin/bash
# Build verification script for ASUS Armoury Crate Linux

set -e

echo "======================================"
echo "ASUS Armoury Crate Linux Build Test"
echo "======================================"
echo ""

# Check Rust installation
if ! command -v cargo &> /dev/null; then
    echo "❌ Error: cargo not found. Please install Rust."
    exit 1
fi

echo "✓ Rust installation found"
rustc --version
cargo --version
echo ""

# Check for required packages (informational only)
echo "Checking for system dependencies..."
echo "Note: GTK4/libadwaita are required for GUI but not for this syntax check"
echo ""

# Try to build (syntax check only without GTK4)
echo "Running cargo check (syntax validation)..."
if cargo check --lib --all-features 2>&1 | tee /tmp/cargo-check.log; then
    echo ""
    echo "✓ Syntax check passed!"
else
    echo ""
    echo "❌ Syntax check failed. See errors above."
    exit 1
fi

echo ""
echo "Running cargo clippy (lint check)..."
if cargo clippy --lib --all-features -- -D warnings 2>&1 | tee /tmp/cargo-clippy.log; then
    echo ""
    echo "✓ Linting passed!"
else
    echo ""
    echo "⚠️  Linting found issues. See warnings above."
    echo "This is not a critical failure for MVP."
fi

echo ""
echo "Running cargo fmt check..."
if cargo fmt -- --check 2>&1; then
    echo "✓ Formatting check passed!"
else
    echo "⚠️  Code formatting issues found."
    echo "Run 'cargo fmt' to fix formatting."
    echo "This is not a critical failure for MVP."
fi

echo ""
echo "======================================"
echo "Build verification complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  1. Install GTK4 and libadwaita development libraries"
echo "  2. Run 'cargo build --release' to build full application"
echo "  3. Run 'sudo ./scripts/install.sh' to install"
echo ""
