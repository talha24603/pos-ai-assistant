import re
from typing import List, Optional
from pydantic import BaseModel, Field

class ChunkMetadata(BaseModel):
    """
    Pydantic model representing structured metadata for a document chunk.
    """
    chunk_index: int = Field(description="The unique index of the chunk in the document")
    content: str = Field(description="The normalized text content of the chunk")
    char_count: int = Field(description="Number of characters in the chunk content")
    overlap_applied: bool = Field(description="Indicates if overlap from the previous chunk was applied")
    section: Optional[str] = Field(default=None, description="The detected document section for this chunk")

def normalize_text(text: str) -> str:
    """
    Normalizes PDF/document text to remove excessive spacing, 
    clean trailing spaces on lines, and collapse redundant newlines
    while preserving meaningful document/paragraph structure.
    """
    if not text:
        return ""
        
    # Standardize carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Normalize excessive horizontal spaces and tabs to a single space
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip leading/trailing spaces from each individual line
    lines = [line.strip() for line in text.split('\n')]
    
    # Compress consecutive empty lines (3 or more) to a single empty line (double newline)
    # This separates paragraphs beautifully without bloated vertical whitespace.
    normalized_lines = []
    consecutive_empty = 0
    for line in lines:
        if not line:
            consecutive_empty += 1
            if consecutive_empty <= 1:
                normalized_lines.append("")
        else:
            consecutive_empty = 0
            normalized_lines.append(line)
            
    return "\n".join(normalized_lines).strip()

def split_by_sections(text: str) -> List[dict]:
    """
    Splits the document text into sections based on common Markdown header patterns
    (e.g., # Header, ## Header, ### Header).
    Each section is returned with its detected section name and text content.
    If no header is found, the text is treated as a single section with section=None.
    """
    # Regex matching Markdown headers at the start of a line
    header_pattern = re.compile(r'^(#{1,6}\s+.+)$', re.MULTILINE)
    
    matches = list(header_pattern.finditer(text))
    
    if not matches:
        return [{"section": None, "content": text}]
        
    sections = []
    
    # Extract any introductory text before the first section header
    first_match = matches[0]
    if first_match.start() > 0:
        intro_content = text[:first_match.start()].strip()
        if intro_content:
            sections.append({"section": None, "content": intro_content})
            
    for i, match in enumerate(matches):
        header_text = match.group(1)
        # Extract section name by removing the leading '#' symbols and whitespace
        section_name = re.sub(r'^#+\s+', '', header_text).strip()
        
        # Calculate the text bounds for this section
        start_idx = match.end()
        end_idx = matches[i+1].start() if i + 1 < len(matches) else len(text)
        
        # We start extracting from the header's start position to preserve the header in content,
        # giving excellent semantic context during RAG search.
        section_content = text[match.start():end_idx].strip()
        
        sections.append({"section": section_name, "content": section_content})
        
    return sections

def split_large_sentence(sentence: str, max_size: int) -> List[str]:
    """
    Recursively/iteratively splits exceptionally long sentences that exceed the `chunk_size`
    into smaller, readable pieces, ensuring no sub-sentence exceeds `max_size`.
    Prefers splitting on sub-sentence punctuation (semicolon, colon, comma), falling back to
    word boundaries (spaces) if no punctuation is available.
    """
    if len(sentence) <= max_size:
        return [sentence]
        
    # Attempt to split on clause punctuation to preserve syntactic integrity: ; : ,
    for punct in [";", ":", ","]:
        if punct in sentence:
            parts = sentence.split(punct)
            # Reconstruct parts with the punctuation restored (except the last one)
            reconstructed_parts = []
            for j in range(len(parts) - 1):
                reconstructed_parts.append(parts[j] + punct)
            reconstructed_parts.append(parts[-1])
            
            # Filter empty parts
            reconstructed_parts = [p.strip() for p in reconstructed_parts if p.strip()]
            
            # Verify if any part is actually smaller than the original.
            if all(len(p) < len(sentence) for p in reconstructed_parts):
                # Now, group the parts into chunks <= max_size
                final_parts = []
                current_part = []
                current_len = 0
                for part in reconstructed_parts:
                    # If a single part itself exceeds max_size, split it recursively
                    if len(part) > max_size:
                        if current_part:
                            final_parts.append(" ".join(current_part))
                            current_part = []
                            current_len = 0
                        final_parts.extend(split_large_sentence(part, max_size))
                    elif current_len + (1 if current_part else 0) + len(part) > max_size:
                        final_parts.append(" ".join(current_part))
                        current_part = [part]
                        current_len = len(part)
                    else:
                        current_part.append(part)
                        current_len += (1 if current_part else 0) + len(part)
                if current_part:
                    final_parts.append(" ".join(current_part))
                return final_parts

    # Fallback: split by word boundaries (spaces)
    words = sentence.split()
    parts = []
    current_part = []
    current_len = 0
    
    for word in words:
        if len(word) > max_size:
            # If word is extremely long, force split
            if current_part:
                parts.append(" ".join(current_part))
                current_part = []
                current_len = 0
            for k in range(0, len(word), max_size):
                parts.append(word[k:k+max_size])
            continue
            
        if current_len + (1 if current_part else 0) + len(word) > max_size:
            parts.append(" ".join(current_part))
            current_part = [word]
            current_len = len(word)
        else:
            current_part.append(word)
            current_len += (1 if current_part else 0) + len(word)
            
    if current_part:
        parts.append(" ".join(current_part))
        
    return parts

def split_into_sentences(text: str) -> List[str]:
    """
    Splits text into individual sentences.
    Avoids splitting on common abbreviations (e.g., Mr., Dr., i.e., e.g.) and initials.
    """
    if not text.strip():
        return []
        
    # Split by standard sentence terminators (. ! ?) followed by whitespace
    raw_sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    
    sentences = []
    temp_sentence = []
    
    abbreviations = {
        "mr.", "mrs.", "ms.", "dr.", "prof.", "sr.", "jr.",
        "inc.", "co.", "ltd.", "corp.", "approx.", "vs.",
        "e.g.", "i.e.", "a.m.", "p.m.", "u.s.", "u.k."
    }
    
    for s in raw_sentences:
        if not s:
            continue
            
        temp_sentence.append(s)
        
        words = s.split()
        if words:
            last_word = words[-1].lower()
            clean_last_word = re.sub(r'^[^\w]+|[^\w.]+$', '', last_word)
            
            is_abbreviation = clean_last_word in abbreviations
            is_initial = len(clean_last_word) == 2 and clean_last_word[0].isalpha() and clean_last_word[1] == '.'
            
            if is_abbreviation or is_initial:
                # Keep accumulating with the next sentence
                continue
                
        # Finalize the sentence
        sentences.append(" ".join(temp_sentence))
        temp_sentence = []
        
    if temp_sentence:
        sentences.append(" ".join(temp_sentence))
        
    return sentences

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[ChunkMetadata]:
    """
    Performs production-grade, section-aware chunking on normalized text.
    
    Features:
    - Normalizes excessive spacing and newlines.
    - Respects Markdown section boundaries (no cross-section chunks or overlaps).
    - Splits oversized sentences into smaller pieces at clause/word boundaries.
    - Generates chunks of at most `chunk_size` characters.
    - Applies `overlap` at sentence boundaries within each section, constrained so
      that overlaps never push the chunk character count beyond `chunk_size`.
    
    Suggested defaults:
    - chunk_size: 500 (focused, semantic retrieval)
    - overlap: 100 (context carryover)
    """
    normalized = normalize_text(text)
    if not normalized:
        return []
        
    sections = split_by_sections(normalized)
    all_chunks = []
    global_chunk_index = 0
    
    for section_info in sections:
        section_name = section_info["section"]
        section_content = section_info["content"]
        
        # Split section content into sentences
        raw_sentences = split_into_sentences(section_content)
        
        # Process sentences to handle oversized ones
        sentences = []
        for sentence in raw_sentences:
            if len(sentence) > chunk_size:
                sentences.extend(split_large_sentence(sentence, chunk_size))
            else:
                sentences.append(sentence)
                
        current_chunk = []
        current_length = 0
        overlap_applied_to_current = False
        
        for sentence in sentences:
            sentence_len = len(sentence)
            
            # If adding this sentence exceeds chunk_size, finalize the current chunk
            if current_length + (1 if current_chunk else 0) + sentence_len > chunk_size:
                if current_chunk:
                    chunk_content = " ".join(current_chunk)
                    all_chunks.append(ChunkMetadata(
                        chunk_index=global_chunk_index,
                        content=chunk_content,
                        char_count=len(chunk_content),
                        overlap_applied=overlap_applied_to_current,
                        section=section_name
                    ))
                    global_chunk_index += 1
                
                # Rollback to create overlap of approximately `overlap` characters
                overlap_chunk = []
                overlap_len = 0
                for prev_s in reversed(current_chunk):
                    next_overlap_len = overlap_len + len(prev_s) + (1 if overlap_chunk else 0)
                    if next_overlap_len <= overlap and next_overlap_len + 1 + sentence_len <= chunk_size:
                        overlap_chunk.insert(0, prev_s)
                        overlap_len = next_overlap_len
                    else:
                        break
                
                current_chunk = overlap_chunk
                current_length = overlap_len
                overlap_applied_to_current = len(overlap_chunk) > 0
                
            current_chunk.append(sentence)
            current_length += (1 if len(current_chunk) > 1 else 0) + sentence_len
            
        # Finalize the last chunk of the section
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            all_chunks.append(ChunkMetadata(
                chunk_index=global_chunk_index,
                content=chunk_content,
                char_count=len(chunk_content),
                overlap_applied=overlap_applied_to_current,
                section=section_name
            ))
            global_chunk_index += 1
            
    return all_chunks