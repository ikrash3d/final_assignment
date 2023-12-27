terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.19.0"
    }
  }

  required_version = ">= 1.2.0"
}

provider "aws" {
  region     = "us-east-1"
  access_key = var.AWS_ACCESS_KEY
  secret_key = var.AWS_SECRET_ACCESS_KEY
}

resource "aws_security_group" "security_group" {
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

resource "aws_security_group" "security_group_trusted_host" {
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port        = 80
    to_port          = 80
    protocol         = "tcp"
    # private ip adress of the gatekeeper
    cidr_blocks      = ["172.31.47.146/32"]
  }

  ingress {
    from_port        = 22
    to_port          = 22
    protocol         = "tcp"
    # private ip adress of the gatekeeper
    cidr_blocks      = ["172.31.47.146/32"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
  }
}

data "aws_vpc" "default" {
  default = true
}

resource "aws_instance" "mysql-stand-alone-server" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./stand_alone_data.sh")
  key_name = "my_key"
  tags = {
    Name = "MySQL Standalone"
  }
}

resource "aws_instance" "mysql-cluster-manager" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./manager_data.sh")
  private_ip             = "172.31.47.224"
  key_name               = "my_key"
  tags = {
    Name = "MySQL Cluster Manager"
  }
}

resource "aws_instance" "mysql-cluster-worker-0" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.32.146"
  key_name               = "my_key"
  tags = {
    Name = "MySQL Cluster Worker-0"
  }
}

resource "aws_instance" "mysql-cluster-worker-1" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.46.175"
  key_name               = "my_key"
  tags = {
    Name = "MySQL Cluster Worker-1"
  }
}

resource "aws_instance" "mysql-cluster-worker-2" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.36.209"
  key_name               = "my_key"
  tags = {
    Name = "MySQL Cluster Worker-2"
  }
}

resource "aws_instance" "proxy"{
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.large"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./proxy_data.sh")
  private_ip             = "172.31.32.165"
  key_name               = "my_key"
  tags = {
    Name = "Proxy"
  }
}

resource "aws_instance" "gatekeeper"{
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.large"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./gatekeeper_data.sh")
  key_name               = "my_key"
  private_ip             = "172.31.47.146"
  tags = {
    Name = "Gatekeeper"
  }
}


resource "aws_instance" "trusted_host"{
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.large"
  vpc_security_group_ids = [aws_security_group.security_group_trusted_host.id]
  availability_zone      = "us-east-1a"
  user_data              = file("./trusted_host_data.sh") 
  key_name               = "my_key"
  private_ip             = "172.31.44.254"
  tags = {
    Name = "Trusted Host"
  }
}

output "proxy_public_ip"{
  value = aws_instance.proxy.public_dns
}

output "gatekeeper_public_ip"{
  value = aws_instance.gatekeeper.public_dns
}

output "trusted_host_public_ip"{
  value = aws_instance.trusted_host.public_dns
}