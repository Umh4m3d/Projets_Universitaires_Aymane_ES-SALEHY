<?php
$message = "Bienvenue sur notre site sécurisé !";
?>

<?php include 'header.php'; ?>

<p><?php echo $message; ?></p>

<p>
    Date and time:
    <?php echo date("Y-m-d H:i:s"); ?>
</p>

<?php include 'footer.php'; ?>
