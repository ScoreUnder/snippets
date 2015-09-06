bigdouble f 0 = 0
bigdouble f x = 2 + (f (x - 1))
double = fix bigdouble
fix f = f (fix f)
