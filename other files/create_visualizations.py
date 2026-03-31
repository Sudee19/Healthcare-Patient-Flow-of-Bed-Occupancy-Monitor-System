#!/usr/bin/env python3
"""
Create visualizations for the Healthcare Occupancy EDA
"""

import sqlite3
import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

def create_visualizations():
    print("📊 Creating visualizations...")
    
    # Load data
    data_path = Path('data/raw')
    db_path = data_path / 'hospital.db'
    json_path = data_path / 'test_events.json'
    
    conn = sqlite3.connect(db_path)
    
    # Load key datasets
    wards_df = pd.read_sql_query("SELECT * FROM wards", conn)
    occupancy_df = pd.read_sql_query("SELECT * FROM ward_occupancy_current", conn)
    sla_df = pd.read_sql_query("SELECT * FROM sla_breaches", conn)
    
    with open(json_path, 'r') as f:
        events_data = json.load(f)
    events_df = pd.DataFrame(events_data)
    
    # Create figure with subplots
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))
    fig.suptitle('Healthcare Occupancy Monitor - Key Metrics', fontsize=16, fontweight='bold')
    
    # 1. Ward Occupancy Status
    wards_summary = wards_df.merge(occupancy_df, on='ward_id', how='left')
    
    colors = ['red' if status == 'critical' else 'orange' if status == 'warning' else 'green' 
              for status in wards_summary['status']]
    
    bars = axes[0,0].barh(wards_summary['ward_name_y'], wards_summary['occupancy_percent'], color=colors)
    axes[0,0].set_title('Current Occupancy by Ward', fontweight='bold')
    axes[0,0].set_xlabel('Occupancy (%)')
    axes[0,0].axvline(x=85, color='black', linestyle='--', alpha=0.7, label='SLA Threshold (85%)')
    axes[0,0].legend()
    
    # Add percentage labels
    for i, (bar, pct) in enumerate(zip(bars, wards_summary['occupancy_percent'])):
        axes[0,0].text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                      f'{pct:.1f}%', va='center')
    
    # 2. Event Type Distribution
    event_counts = events_df['event_type'].value_counts()
    axes[0,1].pie(event_counts.values, labels=event_counts.index, autopct='%1.1f%%', 
                  startangle=90, colors=['#ff9999', '#66b3ff', '#99ff99'])
    axes[0,1].set_title('Event Type Distribution', fontweight='bold')
    
    # 3. Priority Distribution
    priority_counts = events_df['priority'].value_counts()
    colors_priority = ['#ff6b6b', '#4ecdc4', '#45b7d1']
    axes[1,0].pie(priority_counts.values, labels=priority_counts.index, autopct='%1.1f%%',
                  colors=colors_priority)
    axes[1,0].set_title('Patient Priority Distribution', fontweight='bold')
    
    # 4. SLA Breach Duration
    if len(sla_df) > 0:
        breach_wards = sla_df.groupby('ward_name')['consecutive_hours'].mean().sort_values()
        axes[1,1].barh(range(len(breach_wards)), breach_wards.values, color='salmon')
        axes[1,1].set_yticks(range(len(breach_wards)))
        axes[1,1].set_yticklabels(breach_wards.index)
        axes[1,1].set_title('Average SLA Breach Duration by Ward', fontweight='bold')
        axes[1,1].set_xlabel('Hours')
    else:
        axes[1,1].text(0.5, 0.5, 'No SLA Breaches', ha='center', va='center', 
                      transform=axes[1,1].transAxes, fontsize=14)
        axes[1,1].set_title('SLA Breach Duration', fontweight='bold')
    
    plt.tight_layout()
    
    # Save the plot
    output_path = 'healthcare_occupancy_analysis.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved as: {output_path}")
    
    # Show key statistics
    print("\n📈 Key Statistics Summary:")
    print(f"   🏥 Total Wards: {len(wards_df)}")
    print(f"   🛏️  Total Beds: {wards_df['total_beds'].sum()}")
    print(f"   📊 Average Occupancy: {wards_summary['occupancy_percent'].mean():.1f}%")
    print(f"   🔴 Critical Wards: {len(wards_summary[wards_summary['status'] == 'critical'])}")
    print(f"   ⚠️  SLA Breaches: {len(sla_df)}")
    print(f"   📋 Total Events: {len(events_df):,}")
    
    conn.close()
    plt.show()

if __name__ == "__main__":
    create_visualizations()
