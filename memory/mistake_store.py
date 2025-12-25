"""
Mistake Store - Persistent JSON storage for mistakes
"""
import json
from pathlib import Path
from typing import List, Dict, Any
from schemas import Mistake, MemorySnapshot
import config


class MistakeStore:
    """
    Manages persistent storage of mistakes in JSON format
    """
    
    def __init__(self, filepath: Path = None):
        self.filepath = filepath or config.MISTAKES_FILE
        self._ensure_file_exists()
    
    def _ensure_file_exists(self):
        """Create empty mistakes file if it doesn't exist"""
        if not self.filepath.exists():
            initial_data = {
                "mistakes": [],
                "version": "1.0",
                "total_runs": 0,
                "successful_runs": 0
            }
            self.filepath.write_text(json.dumps(initial_data, indent=2))
    
    def load(self) -> MemorySnapshot:
        """Load all mistakes from storage"""
        try:
            data = json.loads(self.filepath.read_text())
            
            # Convert dict mistakes to Mistake objects
            mistakes = [Mistake(**m) for m in data.get("mistakes", [])]
            
            return MemorySnapshot(
                mistakes=mistakes,
                version=data.get("version", "1.0"),
                total_runs=data.get("total_runs", 0),
                successful_runs=data.get("successful_runs", 0)
            )
        
        except Exception as e:
            print(f"⚠️  Error loading mistakes: {e}")
            return MemorySnapshot(mistakes=[], version="1.0")
    
    def save(self, snapshot: MemorySnapshot):
        """Save mistakes to storage"""
        try:
            data = {
                "mistakes": [m.model_dump() for m in snapshot.mistakes],
                "version": snapshot.version,
                "total_runs": snapshot.total_runs,
                "successful_runs": snapshot.successful_runs
            }
            
            self.filepath.write_text(json.dumps(data, indent=2))
        
        except Exception as e:
            print(f"⚠️  Error saving mistakes: {e}")
    
    def add_mistakes(self, new_mistakes: List[Mistake]):
        """Add new mistakes to storage"""
        snapshot = self.load()
        
        # Merge new mistakes, updating frequency for duplicates
        for new_mistake in new_mistakes:
            # Check if this mistake type already exists
            existing = next(
                (m for m in snapshot.mistakes if m.mistake_type == new_mistake.mistake_type),
                None
            )
            
            if existing:
                # Update frequency and timestamp
                existing.frequency += 1
                existing.timestamp = new_mistake.timestamp
            else:
                # Add new mistake
                snapshot.mistakes.append(new_mistake)
        
        # Limit total stored mistakes
        if len(snapshot.mistakes) > config.MAX_MISTAKES_STORED:
            # Keep most frequent mistakes
            snapshot.mistakes = sorted(
                snapshot.mistakes,
                key=lambda m: m.frequency,
                reverse=True
            )[:config.MAX_MISTAKES_STORED]
        
        self.save(snapshot)
    
    def get_recurring_mistakes(self) -> List[Mistake]:
        """Get mistakes that occur frequently"""
        snapshot = self.load()
        return [
            m for m in snapshot.mistakes 
            if m.frequency >= config.MISTAKE_FREQUENCY_THRESHOLD
        ]
    
    def update_stats(self, success: bool):
        """Update run statistics"""
        snapshot = self.load()
        snapshot.total_runs += 1
        if success:
            snapshot.successful_runs += 1
        self.save(snapshot)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        snapshot = self.load()
        
        total = snapshot.total_runs
        successful = snapshot.successful_runs
        
        return {
            "total_runs": total,
            "successful_runs": successful,
            "failed_runs": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "total_mistakes": len(snapshot.mistakes),
            "recurring_patterns": len([m for m in snapshot.mistakes if m.frequency >= 2])
        }
    
    def clear(self):
        """Clear all mistakes (for testing)"""
        snapshot = MemorySnapshot(mistakes=[], version="1.0")
        self.save(snapshot)
