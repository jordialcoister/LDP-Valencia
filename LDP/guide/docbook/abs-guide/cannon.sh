#!/bin/bash
# cannon.sh: Approximating PI by firing cannonballs.

# This is a very simple instance of a "Monte Carlo" simulation,
#+ a mathematical model of a real-life event,
#+ using pseudorandom numbers to emulate random chance.

#  Consider a perfectly square plot of land, 10000 units on a side.
#  This land has a perfectly circular lake in its center,
#+ with a diameter of 10000 units.
#  The plot is actually all water, except for the four corners.
#  (Think of it as a square with an inscribed circle.)
#
#  Let us fire solid iron cannonballs from an old-style cannon
#+ at the square of land.
#  All the shots impact somewhere on the plot of land,
#+ either in the lake or on the dry corners.
#  Since the lake takes up most of the land area,
#+ most of the shots will SPLASH! into the water.
#  Just a few shots will THUD! into solid ground
#+ in the far corners of the land.
#
#  If we take enough random, unaimed shots at the plot of land,
#+ Then the ratio of SPLASHES to total shots will approximate
#+ the value of PI/4
#  Exercise: Explain why.
#
#  Theoretically, the more shots taken, the better the fit.
#  However, a shell script, as opposed to a compiled language
#+ with floating-point math built in, requires a few compromises.
#  This tends to make the simulation less accurate, unfortunately.


DIMENSION=10000  # Length of each side of the plot of land.
                 # Also sets ceiling for random integers generated.

MAXSHOTS=1000    # Fire this many shots.
                 # 10000 or more would be better, but would take too long.
PMULTIPLIER=4.0  # Scaling factor to approximate PI.

get_random ()
{
SEED=$(head -1 /dev/urandom | od -N 1 | awk '{ print $2 }')
RANDOM=$SEED                                  #  From "seeding-random.sh"
                                              #+ example script.
let "rnum = $RANDOM % $DIMENSION"             # Range less than 10000.
echo $rnum
}

distance=        # Declare global variable.
hypotenuse ()    # Calculate hypotenuse of a right triangle.
{                # From "alt-bc.sh" example.
distance=$(bc -l << EOF
scale = 0
sqrt ( $1 * $1 + $2 * $2 )
EOF
)
#  Setting "scale" to zero rounds down result to integer value,
#+ a necessary compromise in this script.
#  This diminshes the accuracy of the simulation, unfortunately.
}


# main() {

# Initialize variables.
shots=0
splashes=0
thuds=0
Pi=0

while [ "$shots" -lt  "$MAXSHOTS" ]           # Main loop.
do

  xCoord=$(get_random)                        # Get random X and Y coords.
  yCoord=$(get_random)
  hypotenuse $xCoord $yCoord                  #  Hypotenuse of right-triangle =
                                              #+ distance.
  ((shots++))

  printf "#%4d   " $shots
  printf "Xc = %4d  " $xCoord
  printf "Yc = %4d  " $yCoord
  printf "Distance = %5d  " $distance         #  Distance from center
                                              #+ of lake.

  if [ "$distance" -le "$DIMENSION" ]
  then
    echo -n "SPLASH!  "
    ((splashes++))
  else
    echo -n "THUD!    "
    ((thuds++))
  fi

  Pi=$(echo "scale=9; $PMULTIPLIER*$splashes/$shots" | bc)
  # Multiply ratio by 4.0.
  echo -n "PI ~ $Pi"
  echo

done

echo
echo "After $shots shots, PI looks like approximately $Pi."
# Tends to run a bit high... 
# Probably due to round-off error and imperfect randomness of $RANDOM.
echo

# }

exit 0

#  One might well wonder whether a shell script is appropriate for
#+ an application as complex and computation-intensive as a simulation.
#
#  There are at least two justifications.
#  1) As a proof of concept: to show it can be done.
#  2) To prototype and test the algorithms before rewriting
#+    it in a compiled high-level language.