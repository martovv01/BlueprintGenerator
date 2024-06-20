from pygame import Vector2
import tkinter as tk
import google.generativeai

canvas: tk.Canvas = None
delta_time: float = 0.01
delta_step: float = 0.1 # 0.01

force_min_threshold: float = 0 # 0.01
canvas_min_move_dst: float = 1
line_friction: float = 0.3

point_radius: int = 10
line_width: int = 5
text_offset_len: int = 30

model: google.generativeai.GenerativeModel
prompt1 = """
You must extract specific information from a geometric problem in a json format. You will use this formal template(you will not change anything, except replace the values where expected based on this description) for writing out the information about points, segments, angles,triangles, rectangles, circles etc.:

Replace <string> and <float> with the appropriate information from the math problem given below.
<string?> and <float?> can be replaced with "?" if the information is not specified.
If unnamed points need names, follow this naming convention:
*rule1* - Points are single letters A, B, C etc; 
*rule2* - circles are k1, k2, k3 etc(you have to name them with one if there is none specified in the math problem description); 
*rule3* - circle centers are O1, O2, O3 etc.(you have to name them with one if there is none specified in the math problem description);
Follow these naming conventions: circles are k1, k2, ...; points are single letters A, B, C, ... .
Rules:
Add rules for all given angles, segment lengths, segment length ratios and points on segments (that are not already defined e.g. on a line etc.).
Angle rules consist of three points and a value (example: angle ABC = ... => "points": ["A", "B", "C"]).
Segment rules consist of two points and a value (example: AB = ... => "points": "["A", "B"]).
Point on line rule consists of three points (example: Z on AB => "points": ["Z", "A", "B"]).
Segment ratio rules consist of four points (example: AB:BC = 3:2 => "points": ["A","B","B","C"] and "value": "3:2")
Parallel lines rule consists of four points(example: ABCD is parallelogram or trapezoid, AB is parallel to CD => "parallel_lines", "points": ["A","B","C","D"])
If there is Height of a point given in the problem, add in the rules section the angle 90 degrees between the point and the side that tle height lies on(example: height from "C" creates point "H" on the side "AB" => "rule_type": "angle","points": ["A", "H", "C"],"value": 90)
If there is a trapezoid in the math problem you should add a parallel lines rule for the parallel sides(exapmle: trapezoid ABCD, thighs AD and BC... => "parallel_lines", "points": ["A","B","C","D"])
If there is Median in the math problem, add in the rules section the ratio of the points to be equal(example: Median from point "A" creates point "M" on the side "BC" => "rule_type": "ratio","points": ["B", "M", "C","M"],"value": "1:1")

Please fill the accurate answers based on the math problem and USE ONLY THE GIVEN TEMPLATE AND DON'T CHANGE ANYTHING, except the values, that are requested! Try to be the most accurate you can be, take your time!
Also, do not surround the response with ```json and ```.

{
  
  "polygons": [
    [<string>, ...], //Here you place exclusively the figure given in the math problem(excluding circles)
    ...
  ],
"additional_lines": [
    [<string>,<string>], // here you place all of the additional lines and exclude the lines from "polygons:[]" array(add them here only if they are not collided with existing sides(example: if there is a triangle ABC, and random point D lies on the line "A,B", than lines "A,D" and "B,D" don't have to be included and you can leave the array blank.
    ...
  ],
  "circles": [ //this is exclusively and only for circles in the math problem(you have to ignore other figures, other than circles)
    {
      "name": <string>,  //follow the instruction *rule2*
      "center_point": <string>, //the center point of the circle(use O1,O2 exc. like described in the description - use *rule2* )
      "inscribed": <bool>,
      "circumscribed": <bool>,
      "figure": [<string>, ...], //here you place the figure, that this circle is inscribed/circumscribed in the same format as you would in "polygons:[]"
      "through_points": [<string>, ...], //if the circle is circumscribed, don't use any of the points of the figure that is circumscribed on, only the ones given in the math problem!(example: if a circle is circumscribed in triangle ABC in the math problem, exclude the points "A","B","C", and only fill if there are ones specified in the given math problem, if there are any given in the math problem, if not, leave the array empty!)
      "radius": <float?> //if it is not specified for the circle, leave the float blank(example: if there is a circle(inscribed/circumscribed) and the radius is not mentioned- leave the radius value to be "?" )!
    },
    ...
  ]
  "rules": [
    {
      "rule_type": "angle" | "segment" | "ratio" | "point_on_segment" | "parallel_lines",
      "points": [<string>,...],
      "value": <string> | <float>
    },
    ...
  ]
}

The math problem is:

Given an rectangle ABCD with AB = 10cm, BC = 2cm, angle ABC = 45 degrees, with inscribed circle, the radius of which is 3cm and point Y is where the circle intersects the rectrangle on side AB with ratio AY to YB 2:3. point H lies on the side AB and is the height of the point C and CH = 5cm. The circle "P" is circumscribed and has a radius 3cm. point M lies on the side BC and is median of the side A

The expected json that you have to return using the template and rules above for this math problem is:

{
  "polygons": [
    ["A", "B", "C", "D"]
  ],
  "additional_lines": [],
  "circles": [
    {
      "name": "P",
      "center_point": "O1",
      "inscribed": false,
      "circumscribed": true,
      "figure": ["A", "B", "C", "D"],
      "through_points": [],
      "radius": 5
    },
    {
      "name": "k1",
      "center_point": "O2",
      "inscribed": true,
      "circumscribed": false,
      "figure": ["A", "B", "C", "D"],
      "through_points": ["Y"],
      "radius": 3
    }
  ],
  "rules": [
    {
      "rule_type": "angle",
      "points": ["A", "B", "C"],
      "value": 45
    },
    {
      "rule_type": "segment",
      "points": ["A", "B"],
      "value": 10
    },
    {
      "rule_type": "segment",
      "points": ["B", "C"],
      "value": 2
    },
    {
      "rule_type": "ratio",
      "points": ["A", "Y", "B", "Y"],
      "value": "2:3"
    },
    {
      "rule_type": "angle",
      "points": ["C", "H", "D"],
      "value": 90
    },
    {
      "rule_type": "segment",
      "points": ["C", "H"],
      "value": 5
    },
    {
      "rule_type": "ratio",
      "points": ["B", "M", "C", "M"],
      "value": "1:1"
    },
    {
      "rule_type": "point_on_segment",
      "points": ["H","A","B"]
    },
    {
      "rule_type": "point_on_segment",
      "points": ["Y","A","B"]
    },
    {
      "rule_type": "point_on_segment",
      "points": ["M","B","C"]
    },
    {
      "rule_type": "parallel_lines",
      "points": ["A", "B", "C", "D"]
    }
  ]
}

Make the same json format using the template and the given example format for this math problem:
"""

prompt = """
You must extract specific information from a geometric problem in a json format. For this, you will fill the json template we provide with information about points, segments, angles, triangles, rectangles, circles etc., while keeping the structure of proper syntax of json.

Here are some rules you need to follow:
Replace <string> and <float> with the appropriate information from the math problem given below.
<string?> and <float?> can be replaced with "?" if the information is not specified.
If unnamed points need names, follow this naming convention:
*rule1* - Points are single letters A, B, C etc.
*rule2* - circles are k1, k2, k3 etc. (you have to name them with one if there is none specified in the math problem description); 
*rule3* - circle centers are O1, O2, O3 etc.(you have to name them with one if there is none specified in the math problem description);
Follow these naming conventions: circles are k1, k2, ...; points are single letters A, B, C, ... .
Rules:
Add rules for all given angles, segment lengths, segment length ratios and points on segments (that are not already defined e.g. on a line etc.).
Angle rules consist of three points and a value (example: angle ABC = ... => "points": ["A", "B", "C"]).
Segment rules consist of two points and a value (example: AB = ... => "points": "["A", "B"]).
Point on line rule consists of three points (example: Z on AB => "points": ["Z", "A", "B"]).
Segment ratio rules consist of four points (example: AB:BC = 3:2 => "points": ["A","B","B","C"] and "value": "3:2")
Parallel lines rule consists of four points(example: ABCD is parallelogram or trapezoid, AB is parallel to CD => "parallel_lines", "points": ["A","B","C", "D"])
If there is height of a point given in the problem, add in the rules section the angle 90 degrees between the point and the side that the height lies on (example: height from "C" creates point "H" on the side "AB" => "rule_type": "angle","points": ["A", "H", "C"],"value": 90)
If there is a trapezoid in the math problem you should add a parallel lines rule for the parallel sides(exapmle: trapezoid ABCD, thighs AD and BC... => "parallel_lines", "points": ["A","B","C","D"])
If there is a median in the math problem, add in the rules section the ratio of the points to be equal(example: median from point "A" creates point "M" on the side "BC" => "rule_type": "ratio","points": ["B", "M", "C", "M"], "value": "1:1")

In the problem, there are unknowns. E.g. when you read "Find angle ABC" or "Find the length of XY" etc., **DO NOT ADD RULES WITH "?" AS VALUE**.
Instead, only add the needed lines to visualize these unknowns, e.g. "additional_lines": [["A", "B"], ["X", "Y"]]

Please fill the accurate answers based on the math problem and USE ONLY THE GIVEN TEMPLATE AND DON'T CHANGE ANYTHING, except the values, that are requested! Try to be the most accurate you can be, take your time!
Also, do not surround the response with ```json and ```.

Here is the json template:

{
  
  "polygons": [
    [<string>, ...], // Place all polygon figures, mentioned in the problem (E.g. triangle ABC and square BCDE => "polygons": [["A", "B", "C"], ["B", "C", "D", "E"]])
    ...
  ],
"additional_lines": [
    [<string>,<string>], // Add any lines, that can not be derived from the polygons, e.g. medians, bisectors, heights, radii, segments between points.
    ...
  ],
  "circles": [
    {
      "name": <string?>,
      "center_point": <string?>,
      "inscribed": <bool>,
      "circumscribed": <bool>,
      "figure": [<string>, ...], // If circle is inscribed or circumscribed: shows in/around which polygon the circle is inscribed/circumscribed
      "through_points": [<string>, ...], // Are there any other additional points that lie on this circle?
      "radius": <float?>
    },
    ...
  ]
  "rules": [
    {
      "rule_type": "angle" | "segment" | "ratio" | "point_on_segment" | "parallel_lines",
      "points": [<string>,...],
      "value": <string> | <float>
    },
    ...
  ]
}

Here is an example of a geometric problem and the output we expect:

Given a rectangle ABCD with AB = 10cm, BC = 2cm, angle ABC = 45 degrees. A circle is inscribed circle in ABCD, the radius of which is 3cm and point Y is where the circle intersects the rectangle on side AB with ratio AY to YB 2:3. Point H lies on the side AB and is the height of the point C and CH = 5cm. The circle "k" is circumscribed and has a radius 3cm. Point M lies on the side BC and is median of the side A. Find angle CAB.

The expected json that you have to return using the template and rules above for this math problem is:

{
  "polygons": [
    ["A", "B", "C", "D"]
  ],
  "additional_lines": [],
  "circles": [
    {
      "name": "k",
      "center_point": "O1",
      "inscribed": false,
      "circumscribed": true,
      "figure": ["A", "B", "C", "D"],
      "through_points": [],
      "radius": 5
    },
    {
      "name": "k1",
      "center_point": "O2",
      "inscribed": true,
      "circumscribed": false,
      "figure": ["A", "B", "C", "D"],
      "through_points": ["Y"],
      "radius": 3
    }
  ],
  "rules": [
    {
      "rule_type": "angle",
      "points": ["A", "B", "C"],
      "value": 45
    },
    {
      "rule_type": "segment",
      "points": ["A", "B"],
      "value": 10
    },
    {
      "rule_type": "segment",
      "points": ["B", "C"],
      "value": 2
    },
    {
      "rule_type": "ratio",
      "points": ["A", "Y", "B", "Y"],
      "value": "2:3"
    },
    {
      "rule_type": "angle",
      "points": ["C", "H", "D"],
      "value": 90
    },
    {
      "rule_type": "segment",
      "points": ["C", "H"],
      "value": 5
    },
    {
      "rule_type": "ratio",
      "points": ["B", "M", "C", "M"],
      "value": "1:1"
    },
    {
      "rule_type": "point_on_segment",
      "points": ["H","A","B"]
    },
    {
      "rule_type": "point_on_segment",
      "points": ["Y","A","B"]
    },
    {
      "rule_type": "point_on_segment",
      "points": ["M","B","C"]
    },
    {
      "rule_type": "parallel_lines",
      "points": ["A", "B", "C", "D"]
    }
  ]
}

Make the same json format using the template and the given example format for the following math problem:"""

prompt1 = ""
# Respond only with this text: "{"polygons": [["A", "B", "C"]], "additional_lines": [], circles": [], "rules": []}"