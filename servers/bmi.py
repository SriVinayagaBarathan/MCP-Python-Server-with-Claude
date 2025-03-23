from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("health_metrics")

# BMI categories and their descriptions
BMI_CATEGORIES = {
    "underweight": {
        "range": "Below 18.5",
        "description": "Being underweight may indicate nutritional deficiencies or other health issues. Consider consulting with a healthcare provider."
    },
    "normal": {
        "range": "18.5 to 24.9",
        "description": "A normal BMI is associated with lower risk of weight-related health problems."
    },
    "overweight": {
        "range": "25.0 to 29.9",
        "description": "Being overweight may increase the risk of certain health conditions. Consider healthy lifestyle changes."
    },
    "obese_class_1": {
        "range": "30.0 to 34.9",
        "description": "Class 1 obesity is associated with increased risk of health problems. Consider consulting with a healthcare provider."
    },
    "obese_class_2": {
        "range": "35.0 to 39.9",
        "description": "Class 2 obesity is associated with high risk of health problems. Medical consultation is recommended."
    },
    "obese_class_3": {
        "range": "40.0 and above",
        "description": "Class 3 obesity (severe) is associated with very high risk of health problems. Medical intervention is recommended."
    }
}

def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI using the formula: weight (kg) / height² (m²)"""
    return weight_kg / (height_m * height_m)

def get_bmi_category(bmi: float) -> Dict[str, str]:
    """Determine BMI category based on the calculated BMI value"""
    if bmi < 18.5:
        return BMI_CATEGORIES["underweight"]
    elif bmi < 25.0:
        return BMI_CATEGORIES["normal"]
    elif bmi < 30.0:
        return BMI_CATEGORIES["overweight"]
    elif bmi < 35.0:
        return BMI_CATEGORIES["obese_class_1"]
    elif bmi < 40.0:
        return BMI_CATEGORIES["obese_class_2"]
    else:
        return BMI_CATEGORIES["obese_class_3"]

@mcp.tool()
async def calculate_bmi_metric(weight_kg: float, height_cm: float) -> str:
    """Calculate BMI using metric measurements.
    
    Args:
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
    """
    # Convert height from cm to meters
    height_m = height_cm / 100
    
    # Calculate BMI
    bmi = calculate_bmi(weight_kg, height_m)
    category = get_bmi_category(bmi)
    
    return f"""
BMI Calculation Results:
------------------------
Weight: {weight_kg} kg
Height: {height_cm} cm ({height_m} m)
BMI: {bmi:.1f}

Category: {category["range"]}
{category["description"]}

Note: BMI is a screening tool and not a diagnostic of body fatness or health.
"""

@mcp.tool()
async def calculate_bmi_imperial(weight_lb: float, height_ft: int, height_in: int = 0) -> str:
    """Calculate BMI using imperial measurements.
    
    Args:
        weight_lb: Weight in pounds
        height_ft: Height (feet component)
        height_in: Height (inches component)
    """
    # Convert imperial to metric
    total_inches = (height_ft * 12) + height_in
    height_m = total_inches * 0.0254
    weight_kg = weight_lb * 0.453592
    
    # Calculate BMI
    bmi = calculate_bmi(weight_kg, height_m)
    category = get_bmi_category(bmi)
    
    return f"""
BMI Calculation Results:
------------------------
Weight: {weight_lb} lbs ({weight_kg:.1f} kg)
Height: {height_ft}'{height_in}" ({total_inches} inches, {height_m:.2f} m)
BMI: {bmi:.1f}

Category: {category["range"]}
{category["description"]}

Note: BMI is a screening tool and not a diagnostic of body fatness or health.
"""

@mcp.tool()
async def get_healthy_weight_range(height_cm: float) -> str:
    """Calculate a healthy weight range based on height using BMI 18.5-24.9.
    
    Args:
        height_cm: Height in centimeters
    """
    height_m = height_cm / 100
    
    # Calculate weight range for BMI 18.5-24.9
    min_weight = 18.5 * (height_m * height_m)
    max_weight = 24.9 * (height_m * height_m)
    
    # Convert to imperial for reference
    height_inches = height_cm * 0.393701
    height_ft = int(height_inches // 12)
    height_in = round(height_inches % 12)
    
    min_weight_lb = min_weight * 2.20462
    max_weight_lb = max_weight * 2.20462
    
    return f"""
Healthy Weight Range Calculation:
--------------------------------
Height: {height_cm} cm ({height_ft}'{height_in}")

Healthy weight range (BMI 18.5-24.9):
{min_weight:.1f} - {max_weight:.1f} kg
{min_weight_lb:.1f} - {max_weight_lb:.1f} lbs

This range is associated with lower risk of weight-related health problems.
Note: Individual factors like muscle mass, body composition, and health conditions 
may affect what's optimal for you. Consult with a healthcare provider for personalized advice.
"""

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')