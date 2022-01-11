locals {
  cluster_name                 = "apn1.k8s.dev.svoe.link"
  master_autoscaling_group_ids = [aws_autoscaling_group.master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link.id]
  master_security_group_ids    = [aws_security_group.masters-apn1-k8s-dev-svoe-link.id]
  masters_role_arn             = aws_iam_role.masters-apn1-k8s-dev-svoe-link.arn
  masters_role_name            = aws_iam_role.masters-apn1-k8s-dev-svoe-link.name
  node_autoscaling_group_ids   = [aws_autoscaling_group.nodes-on-demand-apn1-k8s-dev-svoe-link.id]
  node_security_group_ids      = [aws_security_group.nodes-apn1-k8s-dev-svoe-link.id]
  node_subnet_ids              = ["subnet-08da82d6214c82c18"]
  nodes_role_arn               = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.arn
  nodes_role_name              = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.name
  region                       = "ap-northeast-1"
  subnet_ap-northeast-1a_id    = "subnet-08da82d6214c82c18"
  subnet_ids                   = ["subnet-08da82d6214c82c18"]
  vpc_id                       = "vpc-03822c2081fa070b0"
}

output "cluster_name" {
  value = "apn1.k8s.dev.svoe.link"
}

output "master_autoscaling_group_ids" {
  value = [aws_autoscaling_group.master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link.id]
}

output "master_security_group_ids" {
  value = [aws_security_group.masters-apn1-k8s-dev-svoe-link.id]
}

output "masters_role_arn" {
  value = aws_iam_role.masters-apn1-k8s-dev-svoe-link.arn
}

output "masters_role_name" {
  value = aws_iam_role.masters-apn1-k8s-dev-svoe-link.name
}

output "node_autoscaling_group_ids" {
  value = [aws_autoscaling_group.nodes-on-demand-apn1-k8s-dev-svoe-link.id]
}

output "node_security_group_ids" {
  value = [aws_security_group.nodes-apn1-k8s-dev-svoe-link.id]
}

output "node_subnet_ids" {
  value = ["subnet-08da82d6214c82c18"]
}

output "nodes_role_arn" {
  value = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.arn
}

output "nodes_role_name" {
  value = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.name
}

output "region" {
  value = "ap-northeast-1"
}

output "subnet_ap-northeast-1a_id" {
  value = "subnet-08da82d6214c82c18"
}

output "subnet_ids" {
  value = ["subnet-08da82d6214c82c18"]
}

output "vpc_id" {
  value = "vpc-03822c2081fa070b0"
}

provider "aws" {
  region = "ap-northeast-1"
}

provider "aws" {
  alias  = "files"
  region = "ap-northeast-1"
}

resource "aws_autoscaling_group" "master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link" {
  enabled_metrics = ["GroupDesiredCapacity", "GroupInServiceInstances", "GroupMaxSize", "GroupMinSize", "GroupPendingInstances", "GroupStandbyInstances", "GroupTerminatingInstances", "GroupTotalInstances"]
  launch_template {
    id      = aws_launch_template.master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link.id
    version = aws_launch_template.master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link.latest_version
  }
  max_size              = 1
  metrics_granularity   = "1Minute"
  min_size              = 1
  name                  = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
  protect_from_scale_in = false
  tag {
    key                 = "KubernetesCluster"
    propagate_at_launch = true
    value               = "apn1.k8s.dev.svoe.link"
  }
  tag {
    key                 = "Name"
    propagate_at_launch = true
    value               = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"
    propagate_at_launch = true
    value               = "master-ap-northeast-1a"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/kops-controller-pki"
    propagate_at_launch = true
    value               = ""
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"
    propagate_at_launch = true
    value               = "master"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/control-plane"
    propagate_at_launch = true
    value               = ""
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/master"
    propagate_at_launch = true
    value               = ""
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/node.kubernetes.io/exclude-from-external-load-balancers"
    propagate_at_launch = true
    value               = ""
  }
  tag {
    key                 = "k8s.io/role/master"
    propagate_at_launch = true
    value               = "1"
  }
  tag {
    key                 = "kops.k8s.io/instancegroup"
    propagate_at_launch = true
    value               = "master-ap-northeast-1a"
  }
  tag {
    key                 = "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"
    propagate_at_launch = true
    value               = "owned"
  }
  vpc_zone_identifier = ["subnet-08da82d6214c82c18"]
}

resource "aws_autoscaling_group" "nodes-on-demand-apn1-k8s-dev-svoe-link" {
  enabled_metrics = ["GroupDesiredCapacity", "GroupInServiceInstances", "GroupMaxSize", "GroupMinSize", "GroupPendingInstances", "GroupStandbyInstances", "GroupTerminatingInstances", "GroupTotalInstances"]
  launch_template {
    id      = aws_launch_template.nodes-on-demand-apn1-k8s-dev-svoe-link.id
    version = aws_launch_template.nodes-on-demand-apn1-k8s-dev-svoe-link.latest_version
  }
  max_size              = 2
  metrics_granularity   = "1Minute"
  min_size              = 1
  name                  = "nodes-on-demand.apn1.k8s.dev.svoe.link"
  protect_from_scale_in = false
  tag {
    key                 = "KubernetesCluster"
    propagate_at_launch = true
    value               = "apn1.k8s.dev.svoe.link"
  }
  tag {
    key                 = "Name"
    propagate_at_launch = true
    value               = "nodes-on-demand.apn1.k8s.dev.svoe.link"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"
    propagate_at_launch = true
    value               = "nodes-on-demand"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"
    propagate_at_launch = true
    value               = "node"
  }
  tag {
    key                 = "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/node"
    propagate_at_launch = true
    value               = ""
  }
  tag {
    key                 = "k8s.io/role/node"
    propagate_at_launch = true
    value               = "1"
  }
  tag {
    key                 = "kops.k8s.io/instancegroup"
    propagate_at_launch = true
    value               = "nodes-on-demand"
  }
  tag {
    key                 = "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"
    propagate_at_launch = true
    value               = "owned"
  }
  vpc_zone_identifier = ["subnet-08da82d6214c82c18"]
}

resource "aws_ebs_volume" "a-etcd-events-apn1-k8s-dev-svoe-link" {
  availability_zone = "ap-northeast-1a"
  encrypted         = true
  iops              = 3000
  size              = 20
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "a.etcd-events.apn1.k8s.dev.svoe.link"
    "k8s.io/etcd/events"                           = "a/a"
    "k8s.io/role/master"                           = "1"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
  throughput = 125
  type       = "gp3"
}

resource "aws_ebs_volume" "a-etcd-main-apn1-k8s-dev-svoe-link" {
  availability_zone = "ap-northeast-1a"
  encrypted         = true
  iops              = 3000
  size              = 20
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "a.etcd-main.apn1.k8s.dev.svoe.link"
    "k8s.io/etcd/main"                             = "a/a"
    "k8s.io/role/master"                           = "1"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
  throughput = 125
  type       = "gp3"
}

resource "aws_iam_instance_profile" "masters-apn1-k8s-dev-svoe-link" {
  name = "masters.apn1.k8s.dev.svoe.link"
  role = aws_iam_role.masters-apn1-k8s-dev-svoe-link.name
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "masters.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
}

resource "aws_iam_instance_profile" "nodes-apn1-k8s-dev-svoe-link" {
  name = "nodes.apn1.k8s.dev.svoe.link"
  role = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.name
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "nodes.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
}

resource "aws_iam_role" "masters-apn1-k8s-dev-svoe-link" {
  assume_role_policy = file("${path.module}/data/aws_iam_role_masters.apn1.k8s.dev.svoe.link_policy")
  name               = "masters.apn1.k8s.dev.svoe.link"
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "masters.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
}

resource "aws_iam_role" "nodes-apn1-k8s-dev-svoe-link" {
  assume_role_policy = file("${path.module}/data/aws_iam_role_nodes.apn1.k8s.dev.svoe.link_policy")
  name               = "nodes.apn1.k8s.dev.svoe.link"
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "nodes.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
}

resource "aws_iam_role_policy" "masters-apn1-k8s-dev-svoe-link" {
  name   = "masters.apn1.k8s.dev.svoe.link"
  policy = file("${path.module}/data/aws_iam_role_policy_masters.apn1.k8s.dev.svoe.link_policy")
  role   = aws_iam_role.masters-apn1-k8s-dev-svoe-link.name
}

resource "aws_iam_role_policy" "nodes-apn1-k8s-dev-svoe-link" {
  name   = "nodes.apn1.k8s.dev.svoe.link"
  policy = file("${path.module}/data/aws_iam_role_policy_nodes.apn1.k8s.dev.svoe.link_policy")
  role   = aws_iam_role.nodes-apn1-k8s-dev-svoe-link.name
}

resource "aws_key_pair" "kubernetes-apn1-k8s-dev-svoe-link-aac13af0a95e65bc0e6a0cad89851058" {
  key_name   = "kubernetes.apn1.k8s.dev.svoe.link-aa:c1:3a:f0:a9:5e:65:bc:0e:6a:0c:ad:89:85:10:58"
  public_key = file("${path.module}/data/aws_key_pair_kubernetes.apn1.k8s.dev.svoe.link-aac13af0a95e65bc0e6a0cad89851058_public_key")
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
}

resource "aws_launch_template" "master-ap-northeast-1a-masters-apn1-k8s-dev-svoe-link" {
  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      delete_on_termination = true
      encrypted             = true
      volume_size           = 20
      volume_type           = "gp2"
    }
  }
  iam_instance_profile {
    name = aws_iam_instance_profile.masters-apn1-k8s-dev-svoe-link.id
  }
  image_id      = "ami-08455f1340543554c"
  instance_type = "t3.medium"
  key_name      = aws_key_pair.kubernetes-apn1-k8s-dev-svoe-link-aac13af0a95e65bc0e6a0cad89851058.id
  lifecycle {
    create_before_destroy = true
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = 1
    http_tokens                 = "optional"
  }
  monitoring {
    enabled = false
  }
  name = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
  network_interfaces {
    associate_public_ip_address = true
    delete_on_termination       = true
    ipv6_address_count          = 0
    security_groups             = [aws_security_group.masters-apn1-k8s-dev-svoe-link.id]
  }
  tag_specifications {
    resource_type = "instance"
    tags = {
      "KubernetesCluster"                                                                                     = "apn1.k8s.dev.svoe.link"
      "Name"                                                                                                  = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"                               = "master-ap-northeast-1a"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/kops-controller-pki"                         = ""
      "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"                                      = "master"
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/control-plane"                   = ""
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/master"                          = ""
      "k8s.io/cluster-autoscaler/node-template/label/node.kubernetes.io/exclude-from-external-load-balancers" = ""
      "k8s.io/role/master"                                                                                    = "1"
      "kops.k8s.io/instancegroup"                                                                             = "master-ap-northeast-1a"
      "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                                                          = "owned"
    }
  }
  tag_specifications {
    resource_type = "volume"
    tags = {
      "KubernetesCluster"                                                                                     = "apn1.k8s.dev.svoe.link"
      "Name"                                                                                                  = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"                               = "master-ap-northeast-1a"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/kops-controller-pki"                         = ""
      "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"                                      = "master"
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/control-plane"                   = ""
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/master"                          = ""
      "k8s.io/cluster-autoscaler/node-template/label/node.kubernetes.io/exclude-from-external-load-balancers" = ""
      "k8s.io/role/master"                                                                                    = "1"
      "kops.k8s.io/instancegroup"                                                                             = "master-ap-northeast-1a"
      "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                                                          = "owned"
    }
  }
  tags = {
    "KubernetesCluster"                                                                                     = "apn1.k8s.dev.svoe.link"
    "Name"                                                                                                  = "master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link"
    "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"                               = "master-ap-northeast-1a"
    "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/kops-controller-pki"                         = ""
    "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"                                      = "master"
    "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/control-plane"                   = ""
    "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/master"                          = ""
    "k8s.io/cluster-autoscaler/node-template/label/node.kubernetes.io/exclude-from-external-load-balancers" = ""
    "k8s.io/role/master"                                                                                    = "1"
    "kops.k8s.io/instancegroup"                                                                             = "master-ap-northeast-1a"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                                                          = "owned"
  }
  user_data = filebase64("${path.module}/data/aws_launch_template_master-ap-northeast-1a.masters.apn1.k8s.dev.svoe.link_user_data")
}

resource "aws_launch_template" "nodes-on-demand-apn1-k8s-dev-svoe-link" {
  block_device_mappings {
    device_name = "/dev/sda1"
    ebs {
      delete_on_termination = true
      encrypted             = true
      volume_size           = 20
      volume_type           = "gp2"
    }
  }
  iam_instance_profile {
    name = aws_iam_instance_profile.nodes-apn1-k8s-dev-svoe-link.id
  }
  image_id      = "ami-08455f1340543554c"
  instance_type = "t3.small"
  key_name      = aws_key_pair.kubernetes-apn1-k8s-dev-svoe-link-aac13af0a95e65bc0e6a0cad89851058.id
  lifecycle {
    create_before_destroy = true
  }
  metadata_options {
    http_endpoint               = "enabled"
    http_protocol_ipv6          = "disabled"
    http_put_response_hop_limit = 1
    http_tokens                 = "optional"
  }
  monitoring {
    enabled = false
  }
  name = "nodes-on-demand.apn1.k8s.dev.svoe.link"
  network_interfaces {
    associate_public_ip_address = true
    delete_on_termination       = true
    ipv6_address_count          = 0
    security_groups             = [aws_security_group.nodes-apn1-k8s-dev-svoe-link.id]
  }
  tag_specifications {
    resource_type = "instance"
    tags = {
      "KubernetesCluster"                                                          = "apn1.k8s.dev.svoe.link"
      "Name"                                                                       = "nodes-on-demand.apn1.k8s.dev.svoe.link"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"    = "nodes-on-demand"
      "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"           = "node"
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/node" = ""
      "k8s.io/role/node"                                                           = "1"
      "kops.k8s.io/instancegroup"                                                  = "nodes-on-demand"
      "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                               = "owned"
    }
  }
  tag_specifications {
    resource_type = "volume"
    tags = {
      "KubernetesCluster"                                                          = "apn1.k8s.dev.svoe.link"
      "Name"                                                                       = "nodes-on-demand.apn1.k8s.dev.svoe.link"
      "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"    = "nodes-on-demand"
      "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"           = "node"
      "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/node" = ""
      "k8s.io/role/node"                                                           = "1"
      "kops.k8s.io/instancegroup"                                                  = "nodes-on-demand"
      "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                               = "owned"
    }
  }
  tags = {
    "KubernetesCluster"                                                          = "apn1.k8s.dev.svoe.link"
    "Name"                                                                       = "nodes-on-demand.apn1.k8s.dev.svoe.link"
    "k8s.io/cluster-autoscaler/node-template/label/kops.k8s.io/instancegroup"    = "nodes-on-demand"
    "k8s.io/cluster-autoscaler/node-template/label/kubernetes.io/role"           = "node"
    "k8s.io/cluster-autoscaler/node-template/label/node-role.kubernetes.io/node" = ""
    "k8s.io/role/node"                                                           = "1"
    "kops.k8s.io/instancegroup"                                                  = "nodes-on-demand"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link"                               = "owned"
  }
  user_data = filebase64("${path.module}/data/aws_launch_template_nodes-on-demand.apn1.k8s.dev.svoe.link_user_data")
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-aws-ebs-csi-driver-addons-k8s-io-k8s-1-17" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-aws-ebs-csi-driver.addons.k8s.io-k8s-1.17_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/aws-ebs-csi-driver.addons.k8s.io/k8s-1.17.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-bootstrap" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-bootstrap_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/bootstrap-channel.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-core-addons-k8s-io" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-core.addons.k8s.io_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/core.addons.k8s.io/v1.4.0.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-coredns-addons-k8s-io-k8s-1-12" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-coredns.addons.k8s.io-k8s-1.12_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/coredns.addons.k8s.io/k8s-1.12.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-dns-controller-addons-k8s-io-k8s-1-12" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-dns-controller.addons.k8s.io-k8s-1.12_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/dns-controller.addons.k8s.io/k8s-1.12.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-kops-controller-addons-k8s-io-k8s-1-16" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-kops-controller.addons.k8s.io-k8s-1.16_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/kops-controller.addons.k8s.io/k8s-1.16.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-kubelet-api-rbac-addons-k8s-io-k8s-1-9" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-kubelet-api.rbac.addons.k8s.io-k8s-1.9_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/kubelet-api.rbac.addons.k8s.io/k8s-1.9.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-limit-range-addons-k8s-io" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-limit-range.addons.k8s.io_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/limit-range.addons.k8s.io/v1.5.0.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-networking-cilium-io-k8s-1-16" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-networking.cilium.io-k8s-1.16_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/networking.cilium.io/k8s-1.16-v1.10.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "apn1-k8s-dev-svoe-link-addons-storage-aws-addons-k8s-io-v1-15-0" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_apn1.k8s.dev.svoe.link-addons-storage-aws.addons.k8s.io-v1.15.0_content")
  key                    = "apn1.k8s.dev.svoe.link/addons/storage-aws.addons.k8s.io/v1.15.0.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "cluster-completed-spec" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_cluster-completed.spec_content")
  key                    = "apn1.k8s.dev.svoe.link/cluster-completed.spec"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "etcd-cluster-spec-events" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_etcd-cluster-spec-events_content")
  key                    = "apn1.k8s.dev.svoe.link/backups/etcd/events/control/etcd-cluster-spec"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "etcd-cluster-spec-main" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_etcd-cluster-spec-main_content")
  key                    = "apn1.k8s.dev.svoe.link/backups/etcd/main/control/etcd-cluster-spec"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "kops-version-txt" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_kops-version.txt_content")
  key                    = "apn1.k8s.dev.svoe.link/kops-version.txt"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "manifests-etcdmanager-events" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_manifests-etcdmanager-events_content")
  key                    = "apn1.k8s.dev.svoe.link/manifests/etcd/events.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "manifests-etcdmanager-main" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_manifests-etcdmanager-main_content")
  key                    = "apn1.k8s.dev.svoe.link/manifests/etcd/main.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "manifests-static-kube-apiserver-healthcheck" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_manifests-static-kube-apiserver-healthcheck_content")
  key                    = "apn1.k8s.dev.svoe.link/manifests/static/kube-apiserver-healthcheck.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "nodeupconfig-master-ap-northeast-1a" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_nodeupconfig-master-ap-northeast-1a_content")
  key                    = "apn1.k8s.dev.svoe.link/igconfig/master/master-ap-northeast-1a/nodeupconfig.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_s3_bucket_object" "nodeupconfig-nodes-on-demand" {
  bucket                 = "dev-kops-s3"
  content                = file("${path.module}/data/aws_s3_bucket_object_nodeupconfig-nodes-on-demand_content")
  key                    = "apn1.k8s.dev.svoe.link/igconfig/node/nodes-on-demand/nodeupconfig.yaml"
  provider               = aws.files
  server_side_encryption = "AES256"
}

resource "aws_security_group" "masters-apn1-k8s-dev-svoe-link" {
  description = "Security group for masters"
  name        = "masters.apn1.k8s.dev.svoe.link"
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "masters.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
  vpc_id = "vpc-03822c2081fa070b0"
}

resource "aws_security_group" "nodes-apn1-k8s-dev-svoe-link" {
  description = "Security group for nodes"
  name        = "nodes.apn1.k8s.dev.svoe.link"
  tags = {
    "KubernetesCluster"                            = "apn1.k8s.dev.svoe.link"
    "Name"                                         = "nodes.apn1.k8s.dev.svoe.link"
    "kubernetes.io/cluster/apn1.k8s.dev.svoe.link" = "owned"
  }
  vpc_id = "vpc-03822c2081fa070b0"
}

resource "aws_security_group_rule" "from-0-0-0-0--0-ingress-tcp-22to22-masters-apn1-k8s-dev-svoe-link" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 22
  protocol          = "tcp"
  security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port           = 22
  type              = "ingress"
}

resource "aws_security_group_rule" "from-0-0-0-0--0-ingress-tcp-22to22-nodes-apn1-k8s-dev-svoe-link" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 22
  protocol          = "tcp"
  security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port           = 22
  type              = "ingress"
}

resource "aws_security_group_rule" "from-0-0-0-0--0-ingress-tcp-443to443-masters-apn1-k8s-dev-svoe-link" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 443
  protocol          = "tcp"
  security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port           = 443
  type              = "ingress"
}

resource "aws_security_group_rule" "from-masters-apn1-k8s-dev-svoe-link-egress-all-0to0-0-0-0-0--0" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 0
  protocol          = "-1"
  security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port           = 0
  type              = "egress"
}

resource "aws_security_group_rule" "from-masters-apn1-k8s-dev-svoe-link-egress-all-0to0-__--0" {
  from_port         = 0
  ipv6_cidr_blocks  = ["::/0"]
  protocol          = "-1"
  security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port           = 0
  type              = "egress"
}

resource "aws_security_group_rule" "from-masters-apn1-k8s-dev-svoe-link-ingress-all-0to0-masters-apn1-k8s-dev-svoe-link" {
  from_port                = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port                  = 0
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-masters-apn1-k8s-dev-svoe-link-ingress-all-0to0-nodes-apn1-k8s-dev-svoe-link" {
  from_port                = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  to_port                  = 0
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-egress-all-0to0-0-0-0-0--0" {
  cidr_blocks       = ["0.0.0.0/0"]
  from_port         = 0
  protocol          = "-1"
  security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port           = 0
  type              = "egress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-egress-all-0to0-__--0" {
  from_port         = 0
  ipv6_cidr_blocks  = ["::/0"]
  protocol          = "-1"
  security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port           = 0
  type              = "egress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-ingress-all-0to0-nodes-apn1-k8s-dev-svoe-link" {
  from_port                = 0
  protocol                 = "-1"
  security_group_id        = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port                  = 0
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-ingress-tcp-1to2379-masters-apn1-k8s-dev-svoe-link" {
  from_port                = 1
  protocol                 = "tcp"
  security_group_id        = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port                  = 2379
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-ingress-tcp-2382to4000-masters-apn1-k8s-dev-svoe-link" {
  from_port                = 2382
  protocol                 = "tcp"
  security_group_id        = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port                  = 4000
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-ingress-tcp-4003to65535-masters-apn1-k8s-dev-svoe-link" {
  from_port                = 4003
  protocol                 = "tcp"
  security_group_id        = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port                  = 65535
  type                     = "ingress"
}

resource "aws_security_group_rule" "from-nodes-apn1-k8s-dev-svoe-link-ingress-udp-1to65535-masters-apn1-k8s-dev-svoe-link" {
  from_port                = 1
  protocol                 = "udp"
  security_group_id        = aws_security_group.masters-apn1-k8s-dev-svoe-link.id
  source_security_group_id = aws_security_group.nodes-apn1-k8s-dev-svoe-link.id
  to_port                  = 65535
  type                     = "ingress"
}

terraform {
  required_version = ">= 0.15.0"
  required_providers {
    aws = {
      "configuration_aliases" = [aws.files]
      "source"                = "hashicorp/aws"
      "version"               = ">= 3.59.0"
    }
  }
}
