#!/usr/bin/env python3
"""Analytics script to analyze scraped documents."""

import json
import argparse
import sys
from collections import Counter
from pathlib import Path


def load_documents(filepath: str):
    """Load documents from JSONL file."""
    documents = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
                documents.append(doc)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON on line {line_num}: {e}", file=sys.stderr)
    return documents


def analyze_documents(documents):
    """Analyze and print statistics about documents."""
    if not documents:
        print("No documents to analyze.")
        return
    
    print("="*60)
    print("DOCUMENT ANALYTICS")
    print("="*60)
    
    # Basic counts
    total_docs = len(documents)
    print(f"\nTotal Documents: {total_docs:,}")
    
    # Word counts
    word_counts = [doc["word_count"] for doc in documents]
    char_counts = [doc["char_count"] for doc in documents]
    
    print(f"\nWord Count Statistics:")
    print(f"  Total words: {sum(word_counts):,}")
    print(f"  Average: {sum(word_counts) / len(word_counts):,.0f}")
    print(f"  Median: {sorted(word_counts)[len(word_counts) // 2]:,}")
    print(f"  Min: {min(word_counts):,}")
    print(f"  Max: {max(word_counts):,}")
    
    print(f"\nCharacter Count Statistics:")
    print(f"  Total characters: {sum(char_counts):,}")
    print(f"  Average: {sum(char_counts) / len(char_counts):,.0f}")
    
    # Language distribution
    languages = [doc["language"] for doc in documents]
    lang_counts = Counter(languages)
    print(f"\nLanguage Distribution:")
    for lang, count in lang_counts.most_common():
        percentage = (count / total_docs) * 100
        print(f"  {lang}: {count} ({percentage:.1f}%)")
    
    # Content type distribution
    content_types = [doc["content_type"] for doc in documents]
    type_counts = Counter(content_types)
    print(f"\nContent Type Distribution:")
    for content_type, count in type_counts.most_common():
        percentage = (count / total_docs) * 100
        print(f"  {content_type}: {count} ({percentage:.1f}%)")
    
    # Quality signals
    substantial = sum(1 for doc in documents if doc["is_substantial"])
    long_form = sum(1 for doc in documents if doc["is_long_form"])
    has_code = sum(1 for doc in documents if doc["has_code"])
    
    print(f"\nQuality Signals:")
    print(f"  Substantial (>=100 words): {substantial} ({substantial/total_docs*100:.1f}%)")
    print(f"  Long-form (>=1000 words): {long_form} ({long_form/total_docs*100:.1f}%)")
    print(f"  Contains code: {has_code} ({has_code/total_docs*100:.1f}%)")
    
    # Reading time
    total_reading_time = sum(doc["reading_time_minutes"] for doc in documents)
    avg_reading_time = total_reading_time / total_docs
    print(f"\nReading Time:")
    print(f"  Total estimated reading time: {total_reading_time:,} minutes ({total_reading_time/60:.1f} hours)")
    print(f"  Average per document: {avg_reading_time:.1f} minutes")
    
    # Top documents by word count
    print(f"\nTop 5 Documents by Word Count:")
    sorted_docs = sorted(documents, key=lambda x: x["word_count"], reverse=True)
    for i, doc in enumerate(sorted_docs[:5], 1):
        print(f"  {i}. {doc['title'][:60]}")
        print(f"     URL: {doc['url']}")
        print(f"     Words: {doc['word_count']:,}")
    
    print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze scraped documents and print statistics"
    )
    parser.add_argument(
        "input_file",
        help="Input JSONL file to analyze"
    )
    
    args = parser.parse_args()
    
    if not Path(args.input_file).exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    documents = load_documents(args.input_file)
    analyze_documents(documents)


if __name__ == "__main__":
    main()

