<?php
$a = 60;
$b = 50;

$addition = $a + $b;
$soustraction = $a - $b;
$multiplication = $a * $b;
$division = $a / $b;

echo "Addition: " . $addition . "<br>";
echo "Subtraction: " . $soustraction . "<br>";
echo "Multiplication: " . $multiplication . "<br>";
echo "Division: " . $division . "<br>";

if ($addition > 100) {
    echo "Grand nombre !";
} else {
    echo "Petit nombre.";
}
?>
