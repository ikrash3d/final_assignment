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
  token      = var.AWS_SESSION_TOKEN
}

resource "aws_security_group" "security_group" {
  vpc_id = data.aws_vpc.default.id

  ingress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }
}


data "aws_vpc" "default" {
  default = true
}



resource "aws_instance" "mysql-stand-alone-server" {
  ami                    = "ami-0c7217cdde317cfec"
  instance_type          = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  user_data              = file("./stand_alone_data.sh")
  tags = {
    Name = "MySQL Standalone"
  }
}

resource "aws_instance" "mysql-cluster-manager" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1d"
  user_data              = file("./manager_data.sh")
  private_ip             = "172.31.40.75"
  tags = {
    Name = "MySQL Cluster Manager"
  }
}

resource "aws_instance" "mysql-cluster-worker-0" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1d"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.35.48"
  tags = {
    Name = "MySQL Cluster Worker-0"
  }
}

resource "aws_instance" "mysql-cluster-worker-1" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1d"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.43.247"
  tags = {
    Name = "MySQL Cluster Worker-1"
  }
}

resource "aws_instance" "mysql-cluster-worker-2" {
  ami           = "ami-0c7217cdde317cfec"
  instance_type = "t2.micro"
  vpc_security_group_ids = [aws_security_group.security_group.id]
  availability_zone      = "us-east-1d"
  user_data              = file("./workers_data.sh")
  private_ip             = "172.31.33.114"
  tags = {
    Name = "MySQL Cluster Worker-2"
  }
}
