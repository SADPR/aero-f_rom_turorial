//----------------------------------------------------------------------------//
// 2D Cylinder Mesh                                                           //
//----------------------------------------------------------------------------//

// Geometry parameters

D  = 1;
Lo = 20*D;

clw  = 0.001;
clbg1 = 0.05;
clbg2 = 0.2;
clc  = 2;

dy = 0.01;

Mesh.Algorithm = 8;
Mesh.Optimize = 1;
Mesh.OptimizeThreshold = 0.6;
Mesh.Smoothing = 10;

// Cylinder

Point(1) = {0, -0.5 * dy, 0, clw};
Point(2) = {-0.5*D, -0.5 * dy, 0, clw};
Point(3) = {0, -0.5 * dy, 0.5*D, clw};
Point(4) = {0.5*D, -0.5 * dy, 0, clw};
Point(5) = {0, -0.5 * dy, -0.5*D, clw};
Circle(1) = {2, 1, 3};
Circle(2) = {3, 1, 4};
Circle(3) = {4, 1, 5};
Circle(4) = {5, 1, 2};

// Far-field

Point(6) = {-Lo, -0.5*dy, 0, clc};
Point(7) = {0, -0.5*dy, Lo, clc};
Point(8) = {Lo, -0.5*dy, 0, 0.2*clc};
Point(9) = {0, -0.5*dy, -Lo, clc};
Circle(5) = {6, 1, 7};
Circle(6) = {7, 1, 8};
Circle(7) = {8, 1, 9};
Circle(8) = {9, 1, 6};

// Mid-range (for sizing)

mcr = 0.75*D;
Point(10) = {-mcr, -0.5 * dy, 0, 0.6*clbg1};
Point(11) = {0, -0.5 * dy, mcr, 0.5*clbg1};
Point(12) = {mcr, -0.5 * dy, 0, 0.4*clbg1};
Point(13) = {0, -0.5 * dy, -mcr, 0.5*clbg1};
Circle(9) = {10, 1, 11};
Circle(10) = {11, 1, 12};
Circle(11) = {12, 1, 13};
Circle(12) = {13, 1, 10};

ec = 0*D;
esma = 6.5*D;
esmi = 4.5*D;
Point(14) = {ec, -0.5 * dy, 0};
Point(15) = {ec-esmi, -0.5 * dy, 0, clbg2};
Point(16) = {ec, -0.5 * dy, esmi, clbg2};
Point(17) = {ec+esma, -0.5 * dy, 0, 0.5*clbg2};
Point(18) = {ec, -0.5 * dy, -esmi, clbg2};
Ellipse(13) = {15, 14, 14, 16};
Ellipse(14) = {16, 14, 14, 17};
Ellipse(15) = {17, 14, 14, 18};
Ellipse(16) = {18, 14, 14, 15};

Line(101) = {4,12};
Line(102) = {12,17};
Line(103) = {17,8};
Line(104) = {6,15};
Line(105) = {15,10};
Line(106) = {10,2};

Curve Loop(1) = {1,2,101,-10,-9,106}; Plane Surface(1) = {1};
Curve Loop(2) = {9,10,102,-14,-13,105}; Plane Surface(2) = {2};
Curve Loop(3) = {13,14,103,-6,-5,104}; Plane Surface(3) = {3};
Curve Loop(4) = {3,4,-106,-12,-11,-101}; Plane Surface(4) = {4};
Curve Loop(5) = {11,12,-105,-16,-15,-102}; Plane Surface(5) = {5};
Curve Loop(6) = {15,16,-104,-8,-7,-103}; Plane Surface(6) = {6};

// Extrude volume

out1[] = Extrude {0, dy, 0} { Surface{1}; Layers{1}; };
out2[] = Extrude {0, dy, 0} { Surface{2}; Layers{1}; };
out3[] = Extrude {0, dy, 0} { Surface{3}; Layers{1}; };
out4[] = Extrude {0, dy, 0} { Surface{4}; Layers{1}; };
out5[] = Extrude {0, dy, 0} { Surface{5}; Layers{1}; };
out6[] = Extrude {0, dy, 0} { Surface{6}; Layers{1}; };

Physical Volume("FluidMesh_0") = {out1[1],out2[1],out3[1],out4[1],out5[1],out6[1]};
Physical Surface("Symmetry_1") = {1:6};
Physical Surface("Symmetry_2") = {out1[0],out2[0],out3[0],out4[0],out5[0],out6[0]};
Physical Surface("InletFixed_3") = {out3[6],out6[5]};
Physical Surface("OutletFixed_4") = {out3[5],out6[6]};
Physical Surface("StickMoving_5") = {out1[2], out1[3],out4[2],out4[3]};

